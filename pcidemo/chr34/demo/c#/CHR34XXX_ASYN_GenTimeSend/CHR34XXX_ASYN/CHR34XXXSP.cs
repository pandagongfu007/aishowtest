using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Runtime.InteropServices;

namespace CHR34XXX_ASYN
{
    public struct CHR_DEVBUSST
    {
	    public UInt16 wdDevID;
        public UInt16 wdVenID;
        public UInt16 wdSubDevID;
        public UInt16 wdSubVenID;
        public UInt16 wdBusNum;			//总线号	
        public UInt16 wdDevNum;			//设备号
        public UInt16 wdFunNum;			//功能号
        public UInt16 wdIrqNum;			//中断号
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 12)]
        public ulong[] dwMemBase;//[1]表示起始地址,[0]表示长度(长度为0表示没有)
    };
    public struct CHR_DEVPARST
    {
        public UInt32 dwCardType;
        public UInt32 dwhwVersion;
        public UInt32 dwdvrVersion;
        public UInt32 dwlibVersion;
        public UInt32 dwBoardID;
        public UInt32 dwSN;
        public UInt32 dwChMax;
    };
    public struct CHRUART_DCB_ST
    {
        public UInt32 BaudRate;  //波特率
        public UInt32 ByteSize;  //数据位
        public UInt32 StopBits;  //停止位
        public UInt32 Parity;    //校验位
    };
    public struct CHRUART_ASYN_PROTOCOL_ST
    {
        public Byte ProtocolNo;
        public Byte SFH;
        public Byte EFH;
        public Byte STOF;
        public Byte ETOF;
        public Byte PtlLen;
        public Byte CheckSum;
        public Byte CheckHead;
    };
    public struct CHRUART_SYNC_ERRCHECK_ST
    {
        public int ErrCheckEn;
        public int AddrCheck;
        public int CrcCheck;
        public int WordCheck;
        public int CodeCheck;
        public int LoseCheck;
    };
    public struct CHRUART_SYNC_WORD_ST
    {
        public UInt32 WordCnt;
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 4)]
        public Byte[] FHeader;
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 4)]
        public Byte[] FTail;
    };


    class CHR34XXXAPI
    {
        //板卡操作API
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_OpenDev", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_OpenDev(int devId);   //打开板卡设备
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_OpenDevEx", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_OpenDevEx(ref int devId, Byte busNo, Byte DevNo, Byte FuncNo);   //打开板卡设备
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_CloseDev", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_CloseDev(int devId);   //关闭板卡设备
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_ResetDev", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_ResetDev(int devId);   //复位板卡设备
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_GetDevParInfo", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_GetDevParInfo(int devId, ref CHR_DEVPARST stDevParInfo);    //获取板卡设备信息
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_GetDevBusInfo", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_GetDevBusInfo(int devId, ref CHR_DEVBUSST stDevBusInfo);    //获取板卡总线信息

        //串口通用操作API
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_Ch_SetType", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_Ch_SetType(int devId, Byte Channel, Byte Type);   //串口类型 0:同步串口  1:异步串口
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_Ch_GetType", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_Ch_GetType(int devId, Byte Channel, ref Byte Type);
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_Ch_SetMode", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_Ch_SetMode(int devId, Byte Channel, Byte Mode);   //串口模式 0:232  1:422  2:485
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_Ch_GetMode", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_Ch_GetMode(int devId, Byte Channel,ref Byte Mode);

        //配置串口
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_Ch_SetCommState", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_Ch_SetCommState(int devId, Byte Channel, ref CHRUART_DCB_ST stRsdcb); //配置串口(波特率、数据位、停止位、校验位)
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_Ch_SetFPDIV", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_Ch_SetFPDIV(int devId, Byte Channel, UInt16 FP, UInt16 DIV);
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_Ch_GetFPDIV", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_Ch_GetFPDIV(int devId, Byte Channel, ref UInt16 FP, ref UInt16 DIV);

        //串口发送操作API
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_TxCh_SetMode", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_TxCh_SetMode(int devId, Byte Channel, Byte Mode);       //发送模式 0:单次发送  1:定时发送
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_TxCh_SetPeriod", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_TxCh_SetPeriod(int devId, Byte Channel, UInt32 Period);  //定时发送周期
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_TxCh_FIFOState", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_TxCh_FIFOState(int devId, Byte Channel, ref UInt32 State);  //发送FIFO状态
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_TxCh_FIFOCount", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_TxCh_FIFOCount(int devId, Byte Channel, ref UInt32 FIFOCount);   //发送FIFO数据量
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_TxCh_Write", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_TxCh_Write(int devId, Byte Channel, UInt32 Length, Byte[] Buffer, ref UInt32 pWritten);   //写发送数据
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_TxCh_Start", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_TxCh_Start(int devId, Byte Channel);   //开始定时发送
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_TxCh_Stop", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_TxCh_Stop(int devId, Byte Channel);    //停止定时发送
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_Asyn_TxCh_SetWordGap", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_Asyn_TxCh_SetWordGap(int devId, Byte Channel, UInt32 Gap);  //发送字间隔（仅适用于异步串口）

        //串口接收公共操作API
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_RxCh_ClearOFFlag", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_RxCh_ClearOFFlag(int devId, Byte Channel);  //清空缓冲区溢出标记
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_RxCh_ClearFIFO", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_RxCh_ClearFIFO(int devId, Byte Channel);    //清空接收缓冲区
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_RxCh_Start", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_RxCh_Start(int devId, Byte Channel);        //开始数据接收
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_RxCh_Stop", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_RxCh_Stop(int devId, Byte Channel);         //停止数据接收

        //接收中断操作API
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_RxInt_Enable", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_RxInt_Enable(int devId, Byte Channel, int Enabled);   //接收中断使能
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_Asyn_RxCh_IntDepth", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_Asyn_RxCh_IntDepth(int devId, Byte Channel, UInt32 Depth);  //接收中断触发深度（仅适用于异步串口透明接收）
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_RxInt_CreateEvent", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_RxInt_CreateEvent(int devId, ref IntPtr phEvt);
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_RxInt_WaitEvent", CallingConvention = CallingConvention.StdCall)]
        public extern static UInt32 CHR34XXX_RxInt_WaitEvent(int devId, IntPtr hEvt, UInt32 dwMilliseconds);
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_RxInt_CloseEvent", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_RxInt_CloseEvent(int devId, IntPtr hEvt);

        //异步串口操作API
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_Asyn_Ch_Reset", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_Asyn_Ch_Reset(int devId, Byte Channel);   //通道复位（仅适用于异步串口）
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_Asyn_Ch_RS485LoopBack", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_Asyn_Ch_RS485LoopBack(int devId, Byte Channel, int Enabled);  //485自环模式（仅适用于异步串口）
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_Asyn_RxCh_SetMode", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_Asyn_RxCh_SetMode(int devId, Byte Channel, Byte Mode);  //接收模式 0:透明接收  1:协议接收（仅适用于异步串口）
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_Asyn_RxCh_SetProtocol", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_Asyn_RxCh_SetProtocol(int devId, Byte Channel, ref CHRUART_ASYN_PROTOCOL_ST stFrame);  //设置协议帧（仅适用于异步串口协议接收）

        //异步串口透明接收操作API
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_Asyn_RxCh_FIFOState", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_Asyn_RxCh_FIFOState(int devId, Byte Channel, ref UInt32 State);    //接收FIFO状态（仅适用于异步串口透明接收）
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_Asyn_RxCh_FIFOCount", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_Asyn_RxCh_FIFOCount(int devId, Byte Channel, ref UInt32 Count);    //接收FIFO数据量（仅适用于异步串口透明接收）
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_Asyn_RxCh_Read", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_Asyn_RxCh_Read(int devId, Byte Channel, UInt32 Length, Byte[] Buffer, ref UInt32 Returned);  //读取FIFO数据（仅适用于异步串口透明接收）

        //异步协议&同步串口操作API
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_FM_Ch_TimeOutEn", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_FM_Ch_TimeOutEn(int devId, Byte Channel, Byte Enabled);     //超时丢帧使能
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_FM_Ch_SetTimeOut", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_FM_Ch_SetTimeOut(int devId, Byte Channel, UInt32 TimeOut);   //超时丢帧时间
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_FM_Ch_GetTimeOutCnt", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_FM_Ch_GetTimeOutCnt(int devId, Byte Channel, ref UInt32 Cnt);  //超时丢帧数量
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_FM_Ch_ClearTimeOut", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_FM_Ch_ClearTimeOut(int devId, Byte Channel);                  //超时丢帧清空

        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_FM_Ch_RxMode", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_FM_Ch_RxMode(int devId, Byte Channel, Byte RxMode);         //接收模式 0:FIFO 1:刷新
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_FM_Ch_RxFrmCount", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_FM_Ch_RxFrmCount(int devId, Byte Channel, ref UInt32 FrmCnt);  //缓冲区帧数量
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_FM_Ch_ReadFrm", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_FM_Ch_ReadFrm(int devId, Byte Channel, UInt32 BufSize, Byte[] Buffer, ref UInt32 Returned);        //读取一帧数据（FIFO模式）
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_FM_Ch_ReadRefreshFrm", CallingConvention = CallingConvention.StdCall)]
        public extern static Byte CHR34XXX_FM_Ch_ReadRefreshFrm(int devId, Byte Channel, UInt32 BufSize, Byte[] Buffer, ref UInt32 Returned); //读取最新一帧数据（刷新模式）
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_FM_Ch_ReadMultiFrm", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_FM_Ch_ReadMultiFrm(int devId, Byte Channel, UInt32 FrameCnt, UInt32 BufSize, Byte[] Buffer, ref UInt32 FrmReturned, ref UInt32 BytesReturned);  //读取多帧数据（FIFO模式）

        //同步串口配置操作API
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_Sync_Ch_LocalAddr", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_Sync_Ch_LocalAddr(int devId, Byte Channel, Byte LocalAddr);   //同步串口本地地址
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_Sync_Ch_SetCrc", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_Sync_Ch_SetCrc(int devId, Byte Channel, Byte CrcVal, Byte CrcOrder);   //同步串口CRC设置  
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_Sync_Ch_FrmId", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_Sync_Ch_FrmId(int devId, Byte Channel, UInt16 IdCnt, UInt16 IdPos, UInt16 IdOrder);  //设置同步帧ID
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_Sync_Ch_MonitorEn", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_Sync_Ch_MonitorEn(int devId, Byte Channel, int Enabled);        //同步串口监听模式使能
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_Sync_Ch_TREdge", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_Sync_Ch_TREdge(int devId, Byte Channel, Byte TxEdge, Byte RxEdge);   //设置同步串口时钟边沿(接收时钟边沿和发送时钟边沿必须不同)
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_Sync_Ch_SetSyncWord", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_Sync_Ch_SetSyncWord(int devId, Byte Channel, ref CHRUART_SYNC_WORD_ST stSyncWord);   //设置同步字
        [DllImport("CHR34XXX.dll", EntryPoint = "CHR34XXX_Sync_Ch_SetErrCheck", CallingConvention = CallingConvention.StdCall)]
        public extern static int CHR34XXX_Sync_Ch_SetErrCheck(int devId, Byte Channel, ref CHRUART_SYNC_ERRCHECK_ST stErrCheck);  //同步串口接收错误检测


        [DllImport("CHR34XXX.dll", EntryPoint = "_CHR34XXX_InnerOpen_", CallingConvention = CallingConvention.StdCall)]
        public extern static int _CHR34XXX_InnerOpen_(int devId, ref UInt32 Type, ref CHR_DEVBUSST inBusInfo, ref CHR_DEVPARST inDevInfo);

        //板卡操作API
        public int CHR34XXXSP_OpenDev(int devId)
        { return CHR34XXX_OpenDev(devId); }   //打开板卡设备
        public int CHR34XXXSP_OpenDevEx(ref int devId, Byte busNo, Byte DevNo, Byte FuncNo)
        { return CHR34XXX_OpenDevEx(ref devId, busNo, DevNo, FuncNo); }   //打开板卡设备
        public int CHR34XXXSP_CloseDev(int devId)
        { return CHR34XXX_CloseDev(devId); }   //关闭板卡设备
        public int CHR34XXXSP_ResetDev(int devId)
        { return CHR34XXX_ResetDev(devId); }   //复位板卡设备
        public int CHR34XXXSP_GetDevParInfo(int devId, ref CHR_DEVPARST stDevParInfo)
        { return CHR34XXX_GetDevParInfo(devId, ref stDevParInfo); }    //获取板卡设备信息
        public int CHR34XXXSP_GetDevBusInfo(int devId, ref CHR_DEVBUSST stDevBusInfo)
        { return CHR34XXX_GetDevBusInfo(devId, ref stDevBusInfo); }    //获取板卡总线信息

        //串口通用操作API
        public int CHR34XXXSP_Ch_SetType(int devId, Byte Channel, Byte Type)
        { return CHR34XXX_Ch_SetType(devId, Channel, Type); }   //串口类型 0:同步串口  1:异步串口
        public int CHR34XXXSP_Ch_GetType(int devId, Byte Channel, ref Byte Type)
        { return CHR34XXX_Ch_GetType(devId, Channel, ref Type); }
        public int CHR34XXXSP_Ch_SetMode(int devId, Byte Channel, Byte Mode)
        { return CHR34XXX_Ch_SetMode(devId, Channel, Mode); }   //串口模式 0:232  1:422  2:485
        public int CHR34XXXSP_Ch_GetMode(int devId, Byte Channel, ref Byte Mode)
        { return CHR34XXX_Ch_GetMode(devId, Channel, ref Mode); }

        //配置串口
        public int CHR34XXXSP_Ch_SetCommState(int devId, Byte Channel, ref CHRUART_DCB_ST stRsdcb)
        { return CHR34XXX_Ch_SetCommState(devId, Channel, ref stRsdcb); } //配置串口(波特率、数据位、停止位、校验位)
        public int CHR34XXXSP_Ch_SetFPDIV(int devId, Byte Channel, UInt16 FP, UInt16 DIV)
        { return CHR34XXX_Ch_SetFPDIV(devId, Channel, FP, DIV); }
        public int CHR34XXXSP_Ch_GetFPDIV(int devId, Byte Channel, ref UInt16 FP, ref UInt16 DIV)
        { return CHR34XXX_Ch_GetFPDIV(devId, Channel, ref FP, ref DIV); }

        //串口发送操作API
        public int CHR34XXXSP_TxCh_SetMode(int devId, Byte Channel, Byte Mode)
        { return CHR34XXX_TxCh_SetMode(devId, Channel, Mode); }       //发送模式 0:单次发送  1:定时发送
        public int CHR34XXXSP_TxCh_SetPeriod(int devId, Byte Channel, UInt32 Period)
        { return CHR34XXX_TxCh_SetPeriod(devId, Channel, Period); }  //定时发送周期
        public int CHR34XXXSP_TxCh_FIFOState(int devId, Byte Channel, ref UInt32 State)
        { return CHR34XXX_TxCh_FIFOState(devId, Channel, ref State); }  //发送FIFO状态
        public int CHR34XXXSP_TxCh_FIFOCount(int devId, Byte Channel, ref UInt32 FIFOCount)
        { return CHR34XXX_TxCh_FIFOCount(devId, Channel, ref FIFOCount); }   //发送FIFO数据量
        public int CHR34XXXSP_TxCh_Write(int devId, Byte Channel, UInt32 Length, Byte[] Buffer, ref UInt32 pWritten)
        { return CHR34XXX_TxCh_Write(devId, Channel, Length, Buffer, ref pWritten); }   //写发送数据
        public int CHR34XXXSP_TxCh_Start(int devId, Byte Channel)
        { return CHR34XXX_TxCh_Start(devId, Channel); }   //开始定时发送
        public int CHR34XXXSP_TxCh_Stop(int devId, Byte Channel)
        { return CHR34XXX_TxCh_Stop(devId, Channel); }    //停止定时发送
        public int CHR34XXXSP_Asyn_TxCh_SetWordGap(int devId, Byte Channel, UInt32 Gap)
        { return CHR34XXX_Asyn_TxCh_SetWordGap(devId, Channel, Gap); }  //发送字间隔（仅适用于异步串口）

        //串口接收公共操作API
        public int CHR34XXXSP_RxCh_ClearOFFlag(int devId, Byte Channel)
        { return CHR34XXX_RxCh_ClearOFFlag(devId, Channel); }  //清空缓冲区溢出标记
        public int CHR34XXXSP_RxCh_ClearFIFO(int devId, Byte Channel)
        { return CHR34XXX_RxCh_ClearFIFO(devId, Channel); }    //清空接收缓冲区
        public int CHR34XXXSP_RxCh_Start(int devId, Byte Channel)
        { return CHR34XXX_RxCh_Start(devId, Channel); }        //开始数据接收
        public int CHR34XXXSP_RxCh_Stop(int devId, Byte Channel)
        { return CHR34XXX_RxCh_Stop(devId, Channel); }         //停止数据接收

        //接收中断操作API
        public int CHR34XXXSP_RxInt_Enable(int devId, Byte Channel, int Enabled)
        { return CHR34XXX_RxInt_Enable(devId, Channel, Enabled); }   //接收中断使能
        public int CHR34XXXSP_Asyn_RxCh_IntDepth(int devId, Byte Channel, UInt32 Depth)
        { return CHR34XXX_Asyn_RxCh_IntDepth(devId, Channel, Depth); }  //接收中断触发深度（仅适用于异步串口透明接收）
        public int CHR34XXXSP_RxInt_CreateEvent(int devId, ref IntPtr phEvt)
        { return CHR34XXX_RxInt_CreateEvent(devId, ref phEvt); }
        public UInt32 CHR34XXXSP_RxInt_WaitEvent(int devId, IntPtr hEvt, UInt32 dwMilliseconds)
        { return CHR34XXX_RxInt_WaitEvent(devId, hEvt, dwMilliseconds); }
        public int CHR34XXXSP_RxInt_CloseEvent(int devId, IntPtr hEvt)
        { return CHR34XXX_RxInt_CloseEvent(devId, hEvt); }

        //异步串口操作API
        public int CHR34XXXSP_Asyn_Ch_Reset(int devId, Byte Channel)
        { return CHR34XXX_Asyn_Ch_Reset(devId, Channel); }   //通道复位（仅适用于异步串口）
        public int CHR34XXXSP_Asyn_Ch_RS485LoopBack(int devId, Byte Channel, int Enabled)
        { return CHR34XXX_Asyn_Ch_RS485LoopBack(devId, Channel, Enabled); }  //485自环模式（仅适用于异步串口）
        public int CHR34XXXSP_Asyn_RxCh_SetMode(int devId, Byte Channel, Byte Mode)
        { return CHR34XXX_Asyn_RxCh_SetMode(devId, Channel, Mode); }  //接收模式 0:透明接收  1:协议接收（仅适用于异步串口）
        public int CHR34XXXSP_Asyn_RxCh_SetProtocol(int devId, Byte Channel, ref CHRUART_ASYN_PROTOCOL_ST stFrame)
        { return CHR34XXX_Asyn_RxCh_SetProtocol(devId, Channel, ref stFrame); }  //设置协议帧（仅适用于异步串口协议接收）

        //异步串口透明接收操作API
        public int CHR34XXXSP_Asyn_RxCh_FIFOState(int devId, Byte Channel, ref UInt32 State)
        { return CHR34XXX_Asyn_RxCh_FIFOState(devId, Channel, ref State); }    //接收FIFO状态（仅适用于异步串口透明接收）
        public int CHR34XXXSP_Asyn_RxCh_FIFOCount(int devId, Byte Channel, ref UInt32 Count)
        { return CHR34XXX_Asyn_RxCh_FIFOCount(devId, Channel, ref Count); }    //接收FIFO数据量（仅适用于异步串口透明接收）
        public int CHR34XXXSP_Asyn_RxCh_Read(int devId, Byte Channel, UInt32 Length, Byte[] Buffer, ref UInt32 Returned)
        { return CHR34XXX_Asyn_RxCh_Read(devId, Channel, Length, Buffer, ref Returned); }  //读取FIFO数据（仅适用于异步串口透明接收）

        //异步协议&同步串口操作API
        public int CHR34XXXSP_FM_Ch_TimeOutEn(int devId, Byte Channel, Byte Enabled)
        { return CHR34XXX_FM_Ch_TimeOutEn(devId, Channel, Enabled); }     //超时丢帧使能
        public int CHR34XXXSP_FM_Ch_SetTimeOut(int devId, Byte Channel, UInt32 TimeOut)
        { return CHR34XXX_FM_Ch_SetTimeOut(devId, Channel, TimeOut); }   //超时丢帧时间
        public int CHR34XXXSP_FM_Ch_GetTimeOutCnt(int devId, Byte Channel, ref UInt32 Cnt)
        { return CHR34XXX_FM_Ch_GetTimeOutCnt(devId, Channel, ref Cnt); }  //超时丢帧数量
        public int CHR34XXXSP_FM_Ch_ClearTimeOut(int devId, Byte Channel)
        { return CHR34XXX_FM_Ch_ClearTimeOut(devId, Channel); }                  //超时丢帧清空

        public int CHR34XXXSP_FM_Ch_RxMode(int devId, Byte Channel, Byte RxMode)
        { return CHR34XXX_FM_Ch_RxMode(devId, Channel, RxMode); }         //接收模式 0:FIFO 1:刷新
        public int CHR34XXXSP_FM_Ch_RxFrmCount(int devId, Byte Channel, ref UInt32 FrmCnt)
        { return CHR34XXX_FM_Ch_RxFrmCount(devId, Channel, ref FrmCnt); }  //缓冲区帧数量
        public int CHR34XXXSP_FM_Ch_ReadFrm(int devId, Byte Channel, UInt32 BufSize, Byte[] Buffer, ref UInt32 Returned)
        { return CHR34XXX_FM_Ch_ReadFrm(devId, Channel, BufSize, Buffer, ref Returned); }        //读取一帧数据（FIFO模式）
        public Byte CHR34XXXSP_FM_Ch_ReadRefreshFrm(int devId, Byte Channel, UInt32 BufSize, Byte[] Buffer, ref UInt32 Returned)
        { return CHR34XXX_FM_Ch_ReadRefreshFrm(devId, Channel, BufSize, Buffer, ref Returned); } //读取最新一帧数据（刷新模式）
        public int CHR34XXXSP_FM_Ch_ReadMultiFrm(int devId, Byte Channel, UInt32 FrameCnt, UInt32 BufSize, Byte[] Buffer, ref UInt32 FrmReturned, ref UInt32 BytesReturned)
        { return CHR34XXX_FM_Ch_ReadMultiFrm(devId, Channel, FrameCnt, BufSize, Buffer, ref FrmReturned, ref BytesReturned); }  //读取多帧数据（FIFO模式）

        //同步串口配置操作API
        public int CHR34XXXSP_Sync_Ch_LocalAddr(int devId, Byte Channel, Byte LocalAddr)
        { return CHR34XXX_Sync_Ch_LocalAddr(devId, Channel, LocalAddr); }   //同步串口本地地址
        public int CHR34XXXSP_Sync_Ch_SetCrc(int devId, Byte Channel, Byte CrcVal, Byte CrcOrder)
        { return CHR34XXX_Sync_Ch_SetCrc(devId, Channel, CrcVal, CrcOrder); }   //同步串口CRC设置  
        public int CHR34XXXSP_Sync_Ch_FrmId(int devId, Byte Channel, UInt16 IdCnt, UInt16 IdPos, UInt16 IdOrder)
        { return CHR34XXX_Sync_Ch_FrmId(devId, Channel, IdCnt, IdPos, IdOrder); }  //设置同步帧ID
        public int CHR34XXXSP_Sync_Ch_MonitorEn(int devId, Byte Channel, int Enabled)
        { return CHR34XXX_Sync_Ch_MonitorEn(devId, Channel, Enabled); }        //同步串口监听模式使能
        public int CHR34XXXSP_Sync_Ch_TREdge(int devId, Byte Channel, Byte TxEdge, Byte RxEdge)
        { return CHR34XXX_Sync_Ch_TREdge(devId, Channel, TxEdge, RxEdge); }   //设置同步串口时钟边沿(接收时钟边沿和发送时钟边沿必须不同)
        public int CHR34XXXSP_Sync_Ch_SetSyncWord(int devId, Byte Channel, ref CHRUART_SYNC_WORD_ST stSyncWord)
        { return CHR34XXX_Sync_Ch_SetSyncWord(devId, Channel, ref stSyncWord); }   //设置同步字
        public int CHR34XXXSP_Sync_Ch_SetErrCheck(int devId, Byte Channel, ref CHRUART_SYNC_ERRCHECK_ST stErrCheck)
        { return CHR34XXX_Sync_Ch_SetErrCheck(devId, Channel, ref stErrCheck); }  //同步串口接收错误检测

        public int _CHR34XXXSP_InnerOpen_(int devId, ref UInt32 Type, ref CHR_DEVBUSST inBusInfo, ref CHR_DEVPARST inDevInfo)
        { return _CHR34XXX_InnerOpen_(devId, ref Type, ref inBusInfo, ref inDevInfo); }
    }
}
