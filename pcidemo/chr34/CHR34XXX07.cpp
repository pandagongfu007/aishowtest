// CHR34XXX07_legacy.cpp  —— 兼容老编译器的无 C++11 版本
// 用于 CHR44/CHR34 同类工程中的 CHR34 24路串口板 Demo
// 依赖：./Lib/CHR34XXX_lib.h, .\Lib\CHR34XXX.dll

#include <windows.h>
#include <stdio.h>
#include <string.h>
#include <conio.h>

#include "./Lib/CHR34XXX_lib.h"
#include "demo_types.h"

// ================== 版本查询（纯 C 实现） ==================
static FARPROC FindAnyLegacy(HMODULE h, const char** names, int count) {
    int i;
    for (i = 0; i < count; ++i) {
        if (names[i] && names[i][0]) {
            FARPROC p = GetProcAddress(h, names[i]);
            if (p) return p;
        }
    }
    return NULL;
}
static void PrintVerLineC(const char* tag, const char* v) {
    printf("%s: %s\n", tag, (v && v[0]) ? v : "N/A");
}
static void PrintWithPrefix(const char* prefix, const char* what, const char* v) {
    char buf[64];
    _snprintf(buf, sizeof(buf)-1, "%s %s", prefix, what);
    buf[sizeof(buf)-1] = '\0';
    PrintVerLineC(buf, v);
}
static void QueryAndPrintDllDriverFW_Legacy(
    const wchar_t* dllPath,
    const char*    tagPrefix,
    BYTE           devId,
    const char**   dllFns,   int dllFnCount,    // e.g. {"CHR34XXX_GetDllVersion","CHR34XXX_GetDLLVersion","CHR34XXX_GetDllVer"}
    const char**   drvFns,   int drvFnCount,    // e.g. {"CHR34XXX_GetDriverVersion","CHR34XXX_GetDrvVersion"}
    const char**   fwFns,    int fwFnCount      // e.g. {"CHR34XXX_GetFwVersion","CHR34XXX_GetFirmwareVersion"}
) {
    HMODULE h = LoadLibraryW(dllPath);
    if (!h) {
        wprintf(L"[%hs] LoadLibrary failed: %ls\n", tagPrefix, dllPath);
        return;
    }

    typedef BOOL (__stdcall *GET_STR1)(char*, DWORD);
    typedef BOOL (__stdcall *GET_STR2)(BYTE, char*, DWORD);

    // DLL
    {
        char buf[128]; ZeroMemory(buf, sizeof(buf));
        GET_STR1 p = (GET_STR1)FindAnyLegacy(h, dllFns, dllFnCount);
        if (p) {
            if (p(buf, (DWORD)sizeof(buf))) PrintWithPrefix(tagPrefix, "dll", buf);
            else PrintWithPrefix(tagPrefix, "dll", "query failed");
        } else {
            PrintWithPrefix(tagPrefix, "dll", "not exported");
        }
    }
    // Driver
    {
        char buf[128]; ZeroMemory(buf, sizeof(buf));
        GET_STR1 p = (GET_STR1)FindAnyLegacy(h, drvFns, drvFnCount);
        if (p) {
            if (p(buf, (DWORD)sizeof(buf))) PrintWithPrefix(tagPrefix, "driver", buf);
            else PrintWithPrefix(tagPrefix, "driver", "query failed");
        } else {
            PrintWithPrefix(tagPrefix, "driver", "not exported");
        }
    }
    // FW
    {
        char buf[128]; ZeroMemory(buf, sizeof(buf));
        FARPROC f = FindAnyLegacy(h, fwFns, fwFnCount);
        if (f) {
            BOOL ok = FALSE;
            // 先尝试无需 devId 的签名
            ok = ((GET_STR1)f)(buf, (DWORD)sizeof(buf));
            if (!ok) {
                // 再试带 devId 的版本
                ok = ((GET_STR2)f)(devId, buf, (DWORD)sizeof(buf));
            }
            if (ok) PrintWithPrefix(tagPrefix, "fw", buf);
            else    PrintWithPrefix(tagPrefix, "fw", "query failed");
        } else {
            PrintWithPrefix(tagPrefix, "fw", "not exported");
        }
    }

    FreeLibrary(h);
}
// ================== 版本查询结束 ==================

// ---- forward declarations ----
void initApiParam();

void CHR34xxx_OpenCard();
void CHR34xxx_ResetCard();
void CHR34xxx_CloseCard();

void CHR34xxx_StartSend(BYTE ChNum, BYTE ChWorkMode, RecvCfg* m_recvCfg,
                        SendCfg* m_sendCfg, ptCGF* m_ptCGF,
                        DWORD ASYN_WordGaP, DWORD dwLen, BYTE* TxBuf);
void CHR34xxx_StopSend(BYTE ChNum);

void CHR34xxx_StartRecv(BYTE ChNum, BYTE ChWorkMode, RecvCfg* m_recvCfg,
                        BYTE ASYN_485SelfCk, BYTE ASYN_RecvMode, ptCGF* m_ptCGF);
void CHR34xxx_StopRecv(BYTE ChNum);

void CHR34xxx_RecvData(BYTE ChNum, int is_IntRecv, int is_asynPtRecv,
                       int is_syncMode, int is_FreshRecv, BYTE* Rxbuf, DWORD* dwResult);

void CHR34xxx_send_comm_uartCgf(BYTE ChNum,BYTE ChWorkMode,RecvCfg* m_recvCfg);
void CHR34xxx_recv_comm_uartCgf(BYTE ChNum,BYTE ChWorkMode,RecvCfg* m_recvCfg);
void CHR34xxx_asyn_uartSendCfg(BYTE ChNum, SendCfg* m_sendCfg, DWORD ASYN_WordGaP);
void CHR34xxx_sync_uartSendCfg(BYTE ChNum, SendCfg* m_sendCfg, ptCGF* m_ptCGF);
void CHR34xxx_asyn_uartRecvCfg(BYTE ChNum, RecvCfg* m_recvCfg, BYTE ASYN_485SelfCk, BYTE ASYN_RecvMode, ptCGF* m_ptCGF);
void CHR34xxx_sync_uartRecvCfg(BYTE ChNum, RecvCfg* m_recvCfg, ptCGF* m_ptCGF);
void CHR34xxx_uart_DataSend(BYTE ChNum, SendCfg* m_sendCfg, BYTE ChWorkMode, DWORD dwLen, BYTE* TxBuf);
void CHR34xxx_CardRecvFuc(BYTE ChNum, int is_asynPtRecv, int is_syncMode, int is_FreshRecv, BYTE* Rxbuf, DWORD* dwResult);

#define MaxChNum 8

static BYTE devId = 0;                  // 板卡号
static HANDLE hEvt = NULL;              // 中断句柄
static CHR_DEVPARST stDevParInfo;       // 板卡设备结构体
static CHR_DEVBUSST stDevBusInfo;       // 板卡总线结构体

// 板卡配置参数初始化
static BYTE  ChNum = 0;                 // 测试通道号
static BYTE  ChWorkMode = 0;            // 0=异步, 1=同步
static DWORD ASYN_WordGaP = 8;          // 发送字间隔
static BYTE  ASYN_485SelfCk = 1;        // 485
static DWORD dwLen = 0;                 // 发送数据长度
static BYTE  TxBuf[256];                // 发送buf
static BYTE  Rxbuf[256];                // 接收buf
static DWORD dwResult = 0;              // 实际接收的数据量

static RecvCfg m_recvCfg;
static SendCfg m_sendCfg;
static ptCGF   m_ptCGF;

// =============== 主程序 ===============
int main(int argc, char** argv)
{
    ZeroMemory(&stDevParInfo, sizeof(stDevParInfo));
    ZeroMemory(&stDevBusInfo, sizeof(stDevBusInfo));
    ZeroMemory(&m_recvCfg, sizeof(m_recvCfg));
    ZeroMemory(&m_sendCfg, sizeof(m_sendCfg));
    ZeroMemory(&m_ptCGF,   sizeof(m_ptCGF));

    // 初始化参数
    initApiParam();

    // 打开/复位/打印SN
    CHR34xxx_OpenCard();
    CHR34xxx_ResetCard();
    printf("SN:%X\n", stDevParInfo.dwSN);

    // 版本查询（纯 C 方式）
    {
        const char* dllFns[] = { "CHR34XXX_GetDllVersion", "CHR34XXX_GetDLLVersion", "CHR34XXX_GetDllVer" };
        const char* drvFns[] = { "CHR34XXX_GetDriverVersion", "CHR34XXX_GetDrvVersion" };
        const char* fwFns[]  = { "CHR34XXX_GetFwVersion", "CHR34XXX_GetFirmwareVersion" };
        QueryAndPrintDllDriverFW_Legacy(
            L".\\Lib\\CHR34XXX.dll",
            "CHR34",
            devId,
            dllFns, sizeof(dllFns)/sizeof(dllFns[0]),
            drvFns, sizeof(drvFns)/sizeof(drvFns[0]),
            fwFns,  sizeof(fwFns)/sizeof(fwFns[0])
        );
    }

    // 初始化发送缓冲
    if (m_recvCfg.ASYN_RecvMode == 0) { // 透明模式
        int i;
        dwLen = 10;
        for (i = 0; i < (int)dwLen; ++i) TxBuf[i] = (BYTE)(i + 0xA0);
    } else { // 协议模式
        dwLen = 7;
        TxBuf[0] = 0xa1; TxBuf[1] = 0xa2; TxBuf[2] = 0x03;
        TxBuf[3] = 0x11; TxBuf[4] = 0x22; TxBuf[5] = 0x33; TxBuf[6] = 0x00;
    }

    // 先确保停止
    CHR34xxx_StopSend(ChNum);
    CHR34xxx_StopRecv(ChNum);

    // 启动接收
    CHR34xxx_StartRecv(ChNum, ChWorkMode, &m_recvCfg, ASYN_485SelfCk, m_recvCfg.ASYN_RecvMode, &m_ptCGF);

    // 如为定时发送，启动一次
    if (m_sendCfg.SendMode != 0) {
        CHR34xxx_StartSend(ChNum, ChWorkMode, &m_recvCfg, &m_sendCfg, &m_ptCGF, ASYN_WordGaP, dwLen, TxBuf);
    }

    while(!_kbhit())
    {
        if (m_sendCfg.SendMode == 0) { // 普通发送 -> 每秒发一次
            CHR34xxx_StartSend(ChNum, ChWorkMode, &m_recvCfg, &m_sendCfg, &m_ptCGF, ASYN_WordGaP, dwLen, TxBuf);
        }
        // 接收
        dwResult = 0;
        ZeroMemory(Rxbuf, sizeof(Rxbuf));
        CHR34xxx_RecvData(ChNum, m_recvCfg.RecvIntEn, m_recvCfg.ASYN_RecvMode, ChWorkMode, m_ptCGF.PtRxMode, Rxbuf, &dwResult);

        if (dwResult) {
            DWORD i;
            for (i=0; i<dwResult; ++i) {
                printf("RevData = %x\n", Rxbuf[i]);
            }
        }
        Sleep(1000);
    }
    (void)_getch();

    CHR34xxx_CloseCard();
    return 0;
}

// =============== 参数初始化 ===============
void initApiParam()
{
    // 接收配置
    m_recvCfg.BaudRate      = 115200;   // 2400~1843200 (422/485) / 2400~115200 (232)
    m_recvCfg.Parity        = 0;        // 0:无,1:奇,2:偶
    m_recvCfg.StopNum       = 0;        // 0:1, 1:1.5, 2:2
    m_recvCfg.DataNum       = 8;        // 5~8
    m_recvCfg.ASYN_RecvMode = 1;        // 0:透明 1:协议
    m_recvCfg.IntDeepth     = 5;        // 中断深度
    m_recvCfg.RecvIntEn     = 0;        // 0:禁用中断 1:启用中断
    m_recvCfg.uartMode      = 2;        // 0:RS232 1:RS422 2:RS485
    m_recvCfg.RecvWord16En  = 1;

    // 发送配置
    m_sendCfg.SendMode      = 0;        // 0:普通 1:定时
    m_sendCfg.SendWord16En  = 1;
    m_sendCfg.FrmGap        = 100000;   // us

    // 异步协议
    m_ptCGF.asyn_frame.HDR          = 0xa1;
    m_ptCGF.asyn_frame.EDR          = 0xa2;
    m_ptCGF.asyn_frame.TailA        = 0xb1;
    m_ptCGF.asyn_frame.TailB        = 0xb2;
    m_ptCGF.asyn_frame.LENR         = 3;
    m_ptCGF.asyn_frame.pt_num       = 0;
    m_ptCGF.asyn_frame.SumCheckEN   = 0;
    m_ptCGF.asyn_frame.HeadIncluded = 0;

    // 同步协议
    m_ptCGF.sync_frame.HR[0] = 0xa1; m_ptCGF.sync_frame.HR[1] = 0xa2;
    m_ptCGF.sync_frame.HR[2] = 0xa3; m_ptCGF.sync_frame.HR[3] = 0xa4;
    m_ptCGF.sync_frame.ER[0] = 0xb1; m_ptCGF.sync_frame.ER[1] = 0xb2;
    m_ptCGF.sync_frame.ER[2] = 0xb3; m_ptCGF.sync_frame.ER[3] = 0xb4;

    m_ptCGF.sync_frame.FrameIDCnt      = 4;
    m_ptCGF.sync_frame.FrameIDOrder    = 0;
    m_ptCGF.sync_frame.FrameIDLocation = 3;
    m_ptCGF.sync_frame.LocationAddress = 0;
    m_ptCGF.sync_frame.SYNCWordCnt     = 4;
    m_ptCGF.sync_frame.CRCInitVal      = 1;
    m_ptCGF.sync_frame.CRCOrder        = 0;
    m_ptCGF.sync_frame.ErrFrameEn      = 0;
    m_ptCGF.sync_frame.SendEdge        = 0;
    m_ptCGF.sync_frame.RecvEdge        = 1;
    m_ptCGF.sync_frame.RecvMode        = 0;
    m_ptCGF.sync_frame.AddressTesting  = 0;
    m_ptCGF.sync_frame.CRCTesting      = 0;
    m_ptCGF.sync_frame.SYNCWordTesting = 0;
    m_ptCGF.sync_frame.CodeErrTesting  = 0;
    m_ptCGF.sync_frame.lackCntTesting  = 0;

    // 接收协议
    m_ptCGF.PtRxMode            = 1;    // 0:FIFO 1:刷新
    m_ptCGF.TimeOutThrowFrmEn   = 0;
    m_ptCGF.timeOutCnt          = 0;
}

// =============== 设备操作 ===============
void CHR34xxx_OpenCard()
{
    if(!CHR34XXX_OpenDev(devId)) {
        printf("Error: CHR34XXX_OpenDev\n"); system("pause");
    }
    if(!CHR34XXX_GetDevParInfo(devId,&stDevParInfo)) {
        printf("Error: CHR34XXX_GetDevParInfo\n"); system("pause");
    }
    if(!CHR34XXX_GetDevBusInfo(devId,&stDevBusInfo)) {
        printf("Error: CHR34XXX_GetDevBusInfo\n"); system("pause");
    }
}
void CHR34xxx_ResetCard()
{
    if(!CHR34XXX_ResetDev(devId)) {
        printf("Error: CHR34XXX_ResetDev\n"); // 不强制暂停，避免死停
    }
    if(!CHR34XXX_RxInt_CreateEvent(devId,&hEvt)) {
        printf("Warn: CHR34XXX_RxInt_CreateEvent failed (no INT mode?)\n");
    }
}
void CHR34xxx_CloseCard()
{
    if(hEvt != NULL) CHR34XXX_RxInt_CloseEvent(devId,hEvt);
    CHR34XXX_ResetDev (devId);
    if(!CHR34XXX_CloseDev(devId)) {
        printf("Error: CHR34XXX_CloseDev\n");
    }
}

// =============== 发送/接收配置 ===============
static void set_comm_state_from_recv(BYTE ChNum, RecvCfg* m_recvCfg)
{
    CHRUART_DCB_ST st; ZeroMemory(&st, sizeof(st));
    st.BaudRate = m_recvCfg->BaudRate;
    st.ByteSize = m_recvCfg->DataNum;
    st.StopBits = m_recvCfg->StopNum;
    st.Parity   = m_recvCfg->Parity;
    if(!CHR34XXX_Ch_SetCommState(devId,ChNum,&st)) {
        printf("error: CHR34XXX_Ch_SetCommState\n"); system("pause");
    }
}
void CHR34xxx_send_comm_uartCgf(BYTE ChNum,BYTE ChWorkMode,RecvCfg* m_recvCfg)
{
    if((ChNum % 2) == 0) {
        if(!CHR34XXX_Ch_SetType(devId, (BYTE)(ChNum+1), (ChWorkMode==0)?1:0)) {
            printf("error: CHR34XXX_Ch_SetType\n"); system("pause");
        }
    } else {
        if(!CHR34XXX_Ch_SetType(devId, ChNum, (ChWorkMode==0)?1:0)) {
            printf("error: CHR34XXX_Ch_SetType\n"); system("pause");
        }
    }
    set_comm_state_from_recv(ChNum, m_recvCfg);
}
void CHR34xxx_recv_comm_uartCgf(BYTE ChNum,BYTE ChWorkMode,RecvCfg* m_recvCfg)
{
    if((ChNum % 2) == 0) {
        if(!CHR34XXX_Ch_SetType(devId, (BYTE)(ChNum+1), (ChWorkMode==0)?1:0)) {
            printf("error: CHR34XXX_Ch_SetType\n"); system("pause");
        }
    } else {
        if(!CHR34XXX_Ch_SetType(devId, ChNum, (ChWorkMode==0)?1:0)) {
            printf("error: CHR34XXX_Ch_SetType\n"); system("pause");
        }
    }
    set_comm_state_from_recv(ChNum, m_recvCfg);

    if(m_recvCfg->RecvIntEn) {
        if(!CHR34XXX_RxInt_Enable(devId,ChNum,1)) { printf("error: CHR34XXX_RxInt_Enable\n"); system("pause"); }
    } else {
        if(!CHR34XXX_RxInt_Enable(devId,ChNum,0)) { printf("error: CHR34XXX_RxInt_Enable\n"); system("pause"); }
    }
    if(!CHR34XXX_RxCh_ClearFIFO(devId,ChNum)) { printf("error: CHR34XXX_RxCh_ClearFIFO\n"); }
    if(!CHR34XXX_RxCh_ClearOFFlag(devId,ChNum)) { printf("error: CHR34XXX_RxCh_ClearOFFlag\n"); }
    if(!CHR34XXX_RxCh_Start(devId,ChNum)) { printf("error: CHR34XXX_RxCh_Start\n"); }
}
void CHR34xxx_asyn_uartRecvCfg(BYTE ChNum,RecvCfg* m_recvCfg,BYTE ASYN_485SelfCk,BYTE ASYN_RecvMode,ptCGF* m_ptCGF)
{
    if(!CHR34XXX_Ch_SetMode(devId,ChNum,m_recvCfg->uartMode)) { printf("error: CHR34XXX_Ch_SetMode\n"); }

    if(!CHR34XXX_Asyn_Ch_RS485LoopBack(devId,ChNum,ASYN_485SelfCk)) { printf("error: CHR34XXX_Asyn_Ch_RS485LoopBack\n"); }
    if(!CHR34XXX_Asyn_RxCh_SetMode(devId,ChNum,ASYN_RecvMode))       { printf("error: CHR34XXX_Asyn_RxCh_SetMode\n"); }

    if(!CHR34XXX_FM_Ch_RxMode(devId,ChNum,m_ptCGF->PtRxMode))        { printf("error: CHR34XXX_FM_Ch_RxMode\n"); }

    if(ASYN_RecvMode == 0) {
        if(m_recvCfg->RecvIntEn) {
            if(!CHR34XXX_Asyn_RxCh_IntDepth(devId,ChNum,(BYTE)(m_recvCfg->IntDeepth - 1))) {
                printf("error: CHR34XXX_Asyn_RxCh_IntDepth\n");
            }
        }
    } else {
        CHRUART_ASYN_PROTOCOL_ST st; ZeroMemory(&st, sizeof(st));
        st.CheckSum   = m_ptCGF->asyn_frame.SumCheckEN;
        st.CheckHead  = m_ptCGF->asyn_frame.HeadIncluded;
        st.ProtocolNo = m_ptCGF->asyn_frame.pt_num;
        st.SFH        = m_ptCGF->asyn_frame.HDR;
        st.EFH        = m_ptCGF->asyn_frame.EDR;
        st.STOF       = m_ptCGF->asyn_frame.TailA;
        st.ETOF       = m_ptCGF->asyn_frame.TailB;
        st.PtlLen     = m_ptCGF->asyn_frame.LENR;
        if(!CHR34XXX_Asyn_RxCh_SetProtocol(devId,ChNum,&st)) { printf("error: CHR34XXX_Asyn_RxCh_SetProtocol\n"); }

        if(!CHR34XXX_FM_Ch_TimeOutEn(devId,ChNum,m_ptCGF->TimeOutThrowFrmEn)) { printf("error: CHR34XXX_FM_Ch_TimeOutEn\n"); }
        if(!CHR34XXX_FM_Ch_SetTimeOut(devId,ChNum,m_ptCGF->timeOutCnt))       { printf("error: CHR34XXX_FM_Ch_SetTimeOut\n"); }
        if(!CHR34XXX_FM_Ch_ClearTimeOut(devId,ChNum))                         { printf("error: CHR34XXX_FM_Ch_ClearTimeOut\n"); }
    }
}
void CHR34xxx_sync_uartRecvCfg(BYTE ChNum,RecvCfg* m_recvCfg,ptCGF* m_ptCGF)
{
    if(!CHR34XXX_FM_Ch_RxMode(devId,ChNum,m_ptCGF->PtRxMode)) { printf("error: CHR34XXX_FM_Ch_RxMode\n"); }

    CHRUART_SYNC_WORD_ST sw; ZeroMemory(&sw, sizeof(sw));
    sw.FHeader[0]=m_ptCGF->sync_frame.HR[0]; sw.FHeader[1]=m_ptCGF->sync_frame.HR[1];
    sw.FHeader[2]=m_ptCGF->sync_frame.HR[2]; sw.FHeader[3]=m_ptCGF->sync_frame.HR[3];
    sw.FTail[0]=m_ptCGF->sync_frame.ER[0];   sw.FTail[1]=m_ptCGF->sync_frame.ER[1];
    sw.FTail[2]=m_ptCGF->sync_frame.ER[2];   sw.FTail[3]=m_ptCGF->sync_frame.ER[3];
    sw.WordCnt = m_ptCGF->sync_frame.SYNCWordCnt;

    if(!CHR34XXX_Sync_Ch_SetSyncWord(devId,ChNum,&sw))                         { printf("error: CHR34XXX_Sync_Ch_SetSyncWord\n"); }
    if(!CHR34XXX_Sync_Ch_LocalAddr(devId,ChNum,m_ptCGF->sync_frame.LocationAddress)) { printf("error: CHR34XXX_Sync_Ch_LocalAddr\n"); }
    if(!CHR34XXX_Sync_Ch_SetCrc(devId,ChNum,m_ptCGF->sync_frame.CRCInitVal,m_ptCGF->sync_frame.CRCOrder)) { printf("error: CHR34XXX_Sync_Ch_SetCrc\n"); }
    if(!CHR34XXX_Sync_Ch_TREdge(devId,ChNum,m_ptCGF->sync_frame.SendEdge,m_ptCGF->sync_frame.RecvEdge))   { printf("error: CHR34XXX_Sync_Ch_TREdge\n"); }
    if(!CHR34XXX_Sync_Ch_MonitorEn(devId,ChNum,m_ptCGF->sync_frame.RecvMode))  { printf("error: CHR34XXX_Sync_Ch_MonitorEn\n"); }

    CHRUART_SYNC_ERRCHECK_ST ec; ZeroMemory(&ec, sizeof(ec));
    ec.CrcCheck  = m_ptCGF->sync_frame.CRCTesting;
    ec.AddrCheck = m_ptCGF->sync_frame.AddressTesting;
    ec.CodeCheck = m_ptCGF->sync_frame.CodeErrTesting;
    ec.LoseCheck = m_ptCGF->sync_frame.lackCntTesting;
    ec.WordCheck = m_ptCGF->sync_frame.SYNCWordTesting;
    ec.ErrCheckEn= m_ptCGF->sync_frame.ErrFrameEn;
    if(!CHR34XXX_Sync_Ch_SetErrCheck(devId,ChNum,&ec)) { printf("error: CHR34XXX_Sync_Ch_SetErrCheck\n"); }

    if(!CHR34XXX_FM_Ch_TimeOutEn(devId,ChNum,m_ptCGF->TimeOutThrowFrmEn)) { printf("error: CHR34XXX_FM_Ch_TimeOutEn\n"); }
    if(!CHR34XXX_FM_Ch_SetTimeOut(devId,ChNum,m_ptCGF->timeOutCnt))       { printf("error: CHR34XXX_FM_Ch_SetTimeOut\n"); }
    if(!CHR34XXX_FM_Ch_ClearTimeOut(devId,ChNum))                         { printf("error: CHR34XXX_FM_Ch_ClearTimeOut\n"); }
}
void CHR34xxx_asyn_uartSendCfg(BYTE ChNum,SendCfg* m_sendCfg,DWORD ASYN_WordGaP)
{
    if(!CHR34XXX_TxCh_SetMode(devId,ChNum,m_sendCfg->SendMode)) { printf("error: CHR34XXX_TxCh_SetMode\n"); }
    if(!CHR34XXX_Asyn_TxCh_SetWordGap(devId,ChNum,ASYN_WordGaP)){ printf("error: CHR34XXX_Asyn_TxCh_SetWordGap\n"); }
    if(m_sendCfg->SendMode == 1) {
        if(!CHR34XXX_TxCh_SetPeriod(devId,ChNum,m_sendCfg->FrmGap)) { printf("error: CHR34XXX_TxCh_SetPeriod\n"); }
    }
}
void CHR34xxx_sync_uartSendCfg(BYTE ChNum,SendCfg* m_sendCfg,ptCGF* m_ptCGF)
{
    if(!CHR34XXX_TxCh_SetMode(devId,ChNum,m_sendCfg->SendMode)) { printf("error: CHR34XXX_TxCh_SetMode\n"); }
    if(!CHR34XXX_Sync_Ch_TREdge(devId,ChNum,m_ptCGF->sync_frame.SendEdge,m_ptCGF->sync_frame.RecvEdge)) { printf("error: CHR34XXX_Sync_Ch_TREdge\n"); }

    if(m_sendCfg->SendMode == 1) {
        if(!CHR34XXX_TxCh_SetPeriod(devId,ChNum,m_sendCfg->FrmGap)) { printf("error: CHR34XXX_TxCh_SetPeriod\n"); }
        if(!CHR34XXX_Sync_Ch_FrmId(devId,ChNum,m_ptCGF->sync_frame.FrameIDCnt,m_ptCGF->sync_frame.FrameIDLocation,m_ptCGF->sync_frame.FrameIDOrder)) {
            printf("error: CHR34XXX_Sync_Ch_FrmId\n");
        }
    }
}
void CHR34xxx_StartSend(BYTE ChNum, BYTE ChWorkMode, RecvCfg* m_recvCfg,
                        SendCfg* m_sendCfg, ptCGF* m_ptCGF, DWORD ASYN_WordGaP,
                        DWORD dwLen, BYTE* TxBuf)
{
    CHR34xxx_send_comm_uartCgf(ChNum, ChWorkMode, m_recvCfg);
    if (ChWorkMode == 0) CHR34xxx_asyn_uartSendCfg(ChNum, m_sendCfg, ASYN_WordGaP);
    else                 CHR34xxx_sync_uartSendCfg(ChNum, m_sendCfg, m_ptCGF);
    CHR34xxx_uart_DataSend(ChNum, m_sendCfg, ChWorkMode, dwLen, TxBuf);
}
void CHR34xxx_StopSend(BYTE ChNum)
{
    if(!CHR34XXX_TxCh_Stop(devId,ChNum)) { printf("error: CHR34XXX_TxCh_Stop\n"); }
}
void CHR34xxx_StartRecv(BYTE ChNum,BYTE ChWorkMode,RecvCfg* m_recvCfg,BYTE ASYN_485SelfCk,BYTE ASYN_RecvMode,ptCGF* m_ptCGF)
{
    CHR34xxx_recv_comm_uartCgf(ChNum, ChWorkMode, m_recvCfg);
    if (ChWorkMode == 0) CHR34xxx_asyn_uartRecvCfg(ChNum, m_recvCfg, ASYN_485SelfCk, ASYN_RecvMode, m_ptCGF);
    else                 CHR34xxx_sync_uartRecvCfg(ChNum, m_recvCfg, m_ptCGF);
}
void CHR34xxx_StopRecv(BYTE ChNum)
{
    if(!CHR34XXX_RxCh_Stop(devId,ChNum)) { printf("error: CHR34XXX_RxCh_Stop\n"); }
}
void CHR34xxx_uart_DataSend(BYTE ChNum,SendCfg* m_sendCfg,BYTE ChWorkMode,DWORD dwLen,BYTE* TxBuf)
{
    if(m_sendCfg->SendMode == 0) {
        DWORD Statetmp = 0;
        CHR34XXX_TxCh_FIFOState(devId,ChNum,&Statetmp);
        if((Statetmp & 4) == 0) {
            DWORD wr = 0;
            if(!CHR34XXX_TxCh_Write(devId,ChNum,dwLen,TxBuf,&wr)) printf("error: CHR34XXX_TxCh_Write\n");
        }
    } else {
        CHR34XXX_TxCh_Stop(devId,ChNum);
        DWORD cnt = 0;
        if(!CHR34XXX_TxCh_FIFOCount(devId,ChNum,&cnt)) printf("error: CHR34XXX_TxCh_FIFOCount\n");
        if(cnt == 0) {
            DWORD wr = 0;
            if(!CHR34XXX_TxCh_Write(devId,ChNum,dwLen,TxBuf,&wr)) printf("error: CHR34XXX_TxCh_Write\n");
        }
        CHR34XXX_TxCh_Start(devId,ChNum);
    }
}
void CHR34xxx_CardRecvFuc(BYTE ChNum,int is_asynPtRecv,int is_syncMode,int is_FreshRecv,BYTE* Rxbuf,DWORD* dwResult)
{
    if(is_asynPtRecv || is_syncMode) {
        if(is_FreshRecv == 0) {
            DWORD FrmCnt = 0;
            if(!CHR34XXX_FM_Ch_RxFrmCount(devId,ChNum,&FrmCnt)) printf("error: CHR34XXX_FM_Ch_RxFrmCount\n");
            if(FrmCnt > 0) {
                if(!CHR34XXX_FM_Ch_ReadFrm(devId,ChNum,256,Rxbuf,dwResult)) printf("error: CHR34XXX_FM_Ch_ReadFrm\n");
            }
        } else {
            (void)CHR34XXX_FM_Ch_ReadRefreshFrm(devId,ChNum,256,Rxbuf,dwResult);
        }
        {
            DWORD Cnt = 0;
            if(!CHR34XXX_FM_Ch_GetTimeOutCnt(devId,ChNum,&Cnt)) printf("error: CHR34XXX_FM_Ch_GetTimeOutCnt\n");
        }
    } else {
        DWORD Count = 0;
        if(!CHR34XXX_Asyn_RxCh_FIFOCount(devId,ChNum,&Count)) printf("error: CHR34XXX_Asyn_RxCh_FIFOCount\n");
        if(Count > 0) {
            if(!CHR34XXX_Asyn_RxCh_Read(devId,ChNum,Count,Rxbuf,dwResult)) printf("error: CHR34XXX_Asyn_RxCh_Read\n");
        }
    }
}
void CHR34xxx_RecvData(BYTE ChNum,int is_IntRecv,int is_asynPtRecv,int is_syncMode,int is_FreshRecv,BYTE* Rxbuf,DWORD* dwResult)
{
    if(is_IntRecv) {
        DWORD INFflag = CHR34XXX_RxInt_WaitEvent(devId,hEvt,10);
        int Ch;
        for(Ch = 0; Ch < MaxChNum; ++Ch) {
            if (INFflag & (1u<<Ch)) {
                CHR34xxx_CardRecvFuc((BYTE)Ch, is_asynPtRecv, is_syncMode, is_FreshRecv, Rxbuf, dwResult);
            }
        }
    } else {
        CHR34xxx_CardRecvFuc(ChNum, is_asynPtRecv, is_syncMode, is_FreshRecv, Rxbuf, dwResult);
    }
}

