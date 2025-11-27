import binascii
from typing import List, Dict, Any

# 15400X 系列显示测试设备解析器
#
# 约定：
#   oper="generate_command" 时：
#       必选参数：code, params(list[{"key":..., "value":...}])
#       返回：十六进制字符串（不含空格），直接下发到串口
#   oper="parse_response" 时：
#       必选参数：code, raw(str)
#       返回：dict，供 Atebox 判定和上位机显示使用


def DEV15400(**kwargs) -> Any:
    # -----------------------------------------------------------------------
    # 工具函数（全部作为内部函数，避免被平台当作多个入口）
    # -----------------------------------------------------------------------

    def _get_param_value(params: List[Dict[str, Any]], key: str, default: str = "0") -> str:
        for p in params:
            if p.get("key") == key:
                v = p.get("value", default)
                return str(v)
        return str(default)

    def _get_param_int(params: List[Dict[str, Any]], key: str, default: int = 0) -> int:
        v = _get_param_value(params, key, str(default))
        try:
            return int(v, 0)  # 支持 "10" 或 "0x0A"
        except Exception:
            return default

    def _bytes_to_hex(data: List[int]) -> str:
        return "".join(f"{b & 0xFF:02X}" for b in data)

    def _hex_to_bytes(raw: str) -> List[int]:
        s = str(raw).replace(" ", "").replace("\r", "").replace("\n", "")
        if len(s) < 2:
            return []
        if len(s) % 2 != 0:
            s = s[:-1]
        try:
            return [int(s[i:i + 2], 16) for i in range(0, len(s), 2)]
        except Exception:
            return []

    def _sum_checksum(data: List[int]) -> int:
        """相加取低 8 位"""
        return sum(data) & 0xFF

    def _xor_checksum(data: List[int]) -> int:
        """逐字节 XOR"""
        bp = 0
        for b in data:
            bp ^= (b & 0xFF)
        return bp & 0xFF

    # -----------------------------------------------------------------------
    # 1. 测试机控制帧 / 状态帧
    # -----------------------------------------------------------------------

    def _generate_test_device_control(params: List[Dict[str, Any]]) -> str:
        """
        生成发送给测试设备（15400 测试机）的 24 字节控制帧

        主要参数（十进制或 0x.. 均可）：
            discrete_ctrl        离散量控制字（byte4）
            device_select        设备识别控制字：1->001(0xAA), 2->002(0x55), 3->003(0x66)（byte5）
            crc_fault_ctrl       CRC 错误控制字（byte6）
            freeze_fault_ctrl    画面冻结错误控制字（byte7）
            freeze_on_frames     冻结连续帧数（byte8）
            freeze_off_frames    冻结释放帧数（byte9）
            color_fault_r_ctrl   R 通道异色错误控制字（byte10）
            color_fault_r_on     R 异色连续帧数（byte11）
            color_fault_r_off    R 异色释放帧数（byte12）
            color_fault_g_ctrl   G 控制字（byte13）
            color_fault_g_on     G 连续帧数（byte14）
            color_fault_g_off    G 释放帧数（byte15）
            color_fault_b_ctrl   B 控制字（byte16）
            color_fault_b_on     B 连续帧数（byte17）
            color_fault_b_off    B 释放帧数（byte18）
            timing_fault_ctrl    视频时钟/使能错误控制字（byte19）
            timing_frames        时序错误连续帧数（byte20）
            color_pattern_ctrl   画面颜色控制字（byte21）
        """
        discrete_ctrl = _get_param_int(params, "discrete_ctrl", 0)
        dev_sel = _get_param_int(params, "device_select", 1)
        crc_fault_ctrl = _get_param_int(params, "crc_fault_ctrl", 0)
        freeze_fault_ctrl = _get_param_int(params, "freeze_fault_ctrl", 0)
        freeze_on_frames = _get_param_int(params, "freeze_on_frames", 0)
        freeze_off_frames = _get_param_int(params, "freeze_off_frames", 0)
        cf_r_ctrl = _get_param_int(params, "color_fault_r_ctrl", 0)
        cf_r_on = _get_param_int(params, "color_fault_r_on", 0)
        cf_r_off = _get_param_int(params, "color_fault_r_off", 0)
        cf_g_ctrl = _get_param_int(params, "color_fault_g_ctrl", 0)
        cf_g_on = _get_param_int(params, "color_fault_g_on", 0)
        cf_g_off = _get_param_int(params, "color_fault_g_off", 0)
        cf_b_ctrl = _get_param_int(params, "color_fault_b_ctrl", 0)
        cf_b_on = _get_param_int(params, "color_fault_b_on", 0)
        cf_b_off = _get_param_int(params, "color_fault_b_off", 0)
        timing_fault_ctrl = _get_param_int(params, "timing_fault_ctrl", 0)
        timing_frames = _get_param_int(params, "timing_frames", 0)
        color_pattern_ctrl = _get_param_int(params, "color_pattern_ctrl", 0)

        # 设备识别控制字：001 / 002 / 003
        if dev_sel == 1:
            dev_byte = 0xAA
        elif dev_sel == 2:
            dev_byte = 0x55
        elif dev_sel == 3:
            dev_byte = 0x66
        else:
            # 允许直接给 0xAA/0x55/0x66
            dev_byte = dev_sel & 0xFF

        frame = [
            0xAA,  # header1
            0x55,  # header2
            0x01,  # 固定字
            discrete_ctrl & 0xFF,
            dev_byte & 0xFF,
            crc_fault_ctrl & 0xFF,
            freeze_fault_ctrl & 0xFF,
            freeze_on_frames & 0xFF,
            freeze_off_frames & 0xFF,
            cf_r_ctrl & 0xFF,
            cf_r_on & 0xFF,
            cf_r_off & 0xFF,
            cf_g_ctrl & 0xFF,
            cf_g_on & 0xFF,
            cf_g_off & 0xFF,
            cf_b_ctrl & 0xFF,
            cf_b_on & 0xFF,
            cf_b_off & 0xFF,
            timing_fault_ctrl & 0xFF,
            timing_frames & 0xFF,
            color_pattern_ctrl & 0xFF,
            0x00,  # 预留1
            0x00,  # 预留2
        ]
        checksum = _sum_checksum(frame)  # 前 23 字节相加取低 8 位
        frame.append(checksum)
        return _bytes_to_hex(frame)

    def _parse_test_device_status(raw: str) -> Dict[str, Any]:
        """解析测试设备回传的 17 字节状态帧"""
        data = _hex_to_bytes(raw)
        if len(data) < 17:
            return {"error": "长度不足", "raw": raw}

        if data[0] != 0xAA or data[1] != 0x55 or data[2] != 0x11:
            return {"error": "帧头或固定字错误", "raw": raw}

        expected = ((sum(data[:16]) ^ 0xFF) + 1) & 0xFF
        if expected != (data[16] & 0xFF):
            return {"error": "校验和错误", "raw": raw}

        status_byte = data[3]
        discrete = {
            "dev1_nGo": bool(status_byte & 0x01),
            "dev1_overtemp1": bool(status_byte & 0x02),
            "dev2_nGo": bool(status_byte & 0x04),
            "dev2_overtemp1": bool(status_byte & 0x08),
        }

        dev1_voltage = data[4] + data[5] / 100.0
        dev1_current = data[6] + data[7] / 100.0
        dev2_voltage = data[8] + data[9] / 100.0
        dev2_current = data[10] + data[11] / 100.0

        sw_ver_raw = data[12] & 0xFF
        sw_version = sw_ver_raw & 0x07  # 0~7

        return {
            "discrete": discrete,
            "device1": {
                "voltage": dev1_voltage,
                "current": dev1_current,
            },
            "device2": {
                "voltage": dev2_voltage,
                "current": dev2_current,
            },
            "software_version_raw": sw_ver_raw,
            "software_version": sw_version,
        }

    # -----------------------------------------------------------------------
    # 2. DHA（产品）命令 / 响应（GA, CNT, CMD, DATA..., BP）
    # -----------------------------------------------------------------------

    def _build_dha_frame(cmd: int, data_bytes: List[int], ga: int = 0x00) -> str:
        cnt = 1 + len(data_bytes)  # CMD + DATA
        frame = [ga & 0xFF, cnt & 0xFF, cmd & 0xFF] + [b & 0xFF for b in data_bytes]
        bp = _xor_checksum(frame)
        frame.append(bp)
        return _bytes_to_hex(frame)

    def _generate_dha_command(code: str, params: List[Dict[str, Any]]) -> str:
        ga = _get_param_int(params, "ga", 0x00)

        if code == "dha_set_backlight":
            # mode: 0 关, 1 开
            mode = _get_param_int(params, "mode", 1)
            return _build_dha_frame(0x30, [mode], ga)

        if code == "dha_query_backlight":
            return _build_dha_frame(0x31, [], ga)

        if code == "dha_set_brightness":
            # brightness_fl: 单位 fL，例如 50fL -> 发送 5000
            val_fl = float(_get_param_value(params, "brightness_fl", "50"))
            raw_val = int(round(val_fl * 100.0)) & 0xFFFF
            hi = (raw_val >> 8) & 0xFF
            lo = raw_val & 0xFF
            return _build_dha_frame(0x3C, [hi, lo], ga)

        if code == "dha_query_brightness":
            # kind: 0=实际值, 1=设置值
            kind = _get_param_int(params, "kind", 0)
            return _build_dha_frame(0x3D, [kind], ga)

        if code == "dha_query_ambient":
            return _build_dha_frame(0x3F, [], ga)

        if code == "dha_query_display_mode":
            # 固定 data=0x00
            data0 = _get_param_int(params, "data", 0)
            return _build_dha_frame(0x42, [data0], ga)

        if code == "dha_query_bit":
            # bit_type: 0x0D = DHA BIT, 0x18 = LCD BIT
            bit_type = _get_param_int(params, "bit_type", 0x0D)
            return _build_dha_frame(0x75, [bit_type], ga)

        if code == "dha_heartbeat":
            hb = _get_param_int(params, "value", 0x55)
            return _build_dha_frame(0x78, [hb], ga)

        # 未知 code
        return ""

    def _parse_dha_backlight_resp(raw: str) -> Dict[str, Any]:
        data = _hex_to_bytes(raw)
        if len(data) < 5 or data[2] != 0xB1:
            return {"error": "格式错误", "raw": raw}
        if _xor_checksum(data[:-1]) != data[-1]:
            return {"error": "校验错误", "raw": raw}
        state = data[3]
        return {
            "backlight_raw": state,
            "backlight_on": state == 0x01,
        }

    def _parse_dha_brightness_resp(raw: str) -> Dict[str, Any]:
        data = _hex_to_bytes(raw)
        if len(data) < 7 or data[2] != 0xBD:
            return {"error": "格式错误", "raw": raw}
        if _xor_checksum(data[:-1]) != data[-1]:
            return {"error": "校验错误", "raw": raw}
        kind = data[3]
        val = ((data[4] << 8) | data[5]) / 100.0
        return {
            "kind_raw": kind,
            "kind": "actual" if kind == 0x00 else "set" if kind == 0x01 else "unknown",
            "brightness_fl": val,
        }

    def _parse_dha_ambient_resp(raw: str) -> Dict[str, Any]:
        data = _hex_to_bytes(raw)
        if len(data) < 8 or data[2] != 0xBF:
            return {"error": "格式错误", "raw": raw}
        if _xor_checksum(data[:-1]) != data[-1]:
            return {"error": "校验错误", "raw": raw}
        raw_val = (data[3] << 24) | (data[4] << 16) | (data[5] << 8) | data[6]
        ambient_lux = raw_val / 100.0
        return {
            "ambient_raw": raw_val,
            "ambient_lux": ambient_lux,
        }

    def _parse_dha_display_mode_resp(raw: str) -> Dict[str, Any]:
        data = _hex_to_bytes(raw)
        if len(data) < 6 or data[2] != 0xC2:
            return {"error": "格式错误", "raw": raw}
        if _xor_checksum(data[:-1]) != data[-1]:
            return {"error": "校验错误", "raw": raw}
        src = data[3]
        status = data[4]

        status_map = {
            0x00: "Video invalid (Video OK 低)",
            0x01: "视频时序正确",
            0x02: "无视频输入",
            0x04: "SCPL CRC 出错",
            0x05: "帧计数器出错",
            0x06: "颜色梯度出错",
            0x07: "计数器+颜色梯度出错",
            0x08: "视频时序错误",
            0x09: "时序错误+CRC 出错",
            0x0A: "时序错误+帧计数出错",
            0x0B: "时序错误+颜色梯度出错",
            0x0C: "时序错误+计数和颜色梯度出错",
        }

        return {
            "source_raw": src,
            "status_raw": status,
            "status_desc": status_map.get(status, "未知状态"),
        }

def _parse_dha_bit_resp(raw: str) -> Dict[str, Any]:
    data = _hex_to_bytes(raw)
    if len(data) < 21 or data[2] != 0xF5:
        return {"error": "格式错误", "raw": raw}
    if _xor_checksum(data[:-1]) != data[-1]:
        return {"error": "校验错误", "raw": raw}

    bit_type = data[3]                 # 0x0D: DHA BIT, 0x18: LCD BIT
    bytes_data = data[4:-1]            # DATA1..DATA16（16 字节 = 64 个 2bit 位）

    # 解析出 64 个 2-bit 的 BIT 结果（0 未测，1 通过，2 失败）
    bits: List[int] = []
    for b in bytes_data:
        for shift in (0, 2, 4, 6):
            bits.append((b >> shift) & 0x03)

    # 统计
    pass_count = sum(1 for v in bits if v == 0x01)
    fail_count = sum(1 for v in bits if v == 0x02)
    not_test_count = sum(1 for v in bits if v == 0x00)

    # 索引（1..64）→ 名称/说明 映射，仅填入你给到的表
    name_map = {
        9:  ("DHA_BIT9",  "视频数据CRC状态"),
        10: ("DHA_BIT10", "视频画面冻结检测功能"),
        11: ("DHA_BIT11", "视频颜色梯度状态"),
        14: ("DHA_BIT14", "奇像素视频数据时钟状态"),
        15: ("DHA_BIT15", "偶像素视频数据时钟状态"),
        16: ("DHA_BIT16", "奇像素视频数据使能状态"),
        17: ("DHA_BIT17", "偶像素视频数据使能状态"),
        18: ("DHA_BIT18", "LED状态"),
        19: ("DHA_BIT19", "FPGA初始化状态"),
        20: ("DHA_BIT20", "环境光亮度传感器IIC通讯状态"),
        21: ("DHA_BIT21", "FPGA SPI通讯状态"),
        22: ("DHA_BIT22", "NVRAM SPI通讯状态"),
        23: ("DHA_BIT23", "nGo状态"),
        24: ("DHA_BIT24", "nOvertemp状态"),
        25: ("DHA_BIT25", "VideoOK状态"),
        26: ("DHA_BIT26", "PowerOK状态"),
        27: ("LCD_BIT27", "LCD状态"),
    }

    # 组装“失败/成功 BIT 的字符串列表”
    fail_list: List[str] = []
    pass_list: List[str] = []
    for idx, v in enumerate(bits, start=1):   # idx: 1..64
        if idx in name_map:
            name, desc = name_map[idx]
            if v == 0x02:
                fail_list.append(f"{name}({desc})")
            elif v == 0x01:
                pass_list.append(f"{name}({desc})")

    return {
        "bit_type_raw": bit_type,
        "bit_type": "DHA" if bit_type == 0x0D else "LCD" if bit_type == 0x18 else "UNKNOWN",
        "bits": bits,                          # 长度 64（0=未测,1=通过,2=失败）
        "pass_count": pass_count,
        "fail_count": fail_count,
        "not_test_count": not_test_count,
        "bit_fail_str": "、".join(fail_list) if fail_list else "",
        "bit_pass_str": "、".join(pass_list) if pass_list else "",
    }


    def _parse_dha_heartbeat_resp(raw: str) -> Dict[str, Any]:
        data = _hex_to_bytes(raw)
        if len(data) < 5 or data[2] != 0xF8:
            return {"error": "格式错误", "raw": raw}
        if _xor_checksum(data[:-1]) != data[-1]:
            return {"error": "校验错误", "raw": raw}
        value = data[3]
        return {
            "heartbeat_value": value,
        }

    # -----------------------------------------------------------------------
    # 3. 总入口包装（在本文件内部使用）
    # -----------------------------------------------------------------------

    def generate_command(code: str, params: List[Dict[str, Any]]) -> str:
        if code == "test_device_ctrl":
            return _generate_test_device_control(params)
        # 其余全部走 DHA 命令
        return _generate_dha_command(code, params)

    def parse_response(code: str, raw: str) -> Dict[str, Any]:
        if code == "test_device_status":
            return _parse_test_device_status(raw)
        if code == "dha_backlight_resp":
            return _parse_dha_backlight_resp(raw)
        if code == "dha_brightness_resp":
            return _parse_dha_brightness_resp(raw)
        if code == "dha_ambient_resp":
            return _parse_dha_ambient_resp(raw)
        if code == "dha_display_mode_resp":
            return _parse_dha_display_mode_resp(raw)
        if code == "dha_bit_resp":
            return _parse_dha_bit_resp(raw)
        if code == "dha_heartbeat_resp":
            return _parse_dha_heartbeat_resp(raw)
        return {"raw": raw}

    # -----------------------------------------------------------------------
    # 4. 真正对外暴露的入口（Atebox 只看到这一层）
    # -----------------------------------------------------------------------

    oper = kwargs.get("oper", "")
    if oper == "generate_command":
        code = kwargs.get("code", "")
        params = kwargs.get("params", []) or []
        return generate_command(code, params)

    if oper == "parse_response":
        code = kwargs.get("code", "")
        raw = kwargs.get("raw", "") or ""
        return parse_response(code, raw)

    return ""
