// CHR34XXX01.cpp : 定义控制台应用程序的入口点。
//

#include "stdafx.h"
#include "../Lib/CHR34XXX_lib.h"
#include <conio.h>

#define MaxChNum 8

BYTE devId = 0;//板卡号
HANDLE hEvt = NULL;//中断句柄
CHR_DEVPARST stDevParInfo = {0};//板卡设备结构体
CHR_DEVBUSST stDevBusInfo = {0};//板卡总线结构体

//板卡配置参数初始化
BYTE ChNum = 0;//测试通道号
BYTE ChWorkMode = 0;//异步模式
DWORD ASYN_WordGaP = 8;//发送字间隔
BYTE ASYN_485SelfCk = 1;//485
DWORD dwLen = 0;//发送数据长度
BYTE TxBuf[256] = {0};//发送buf
BYTE Rxbuf[256] = {0};//接收buf
DWORD dwResult = 0;//实际接收的数据量
RecvCfg m_recvCfg = {0};//接收配置结构体
SendCfg m_sendCfg = {0};//发送配置结构体
ptCGF m_ptCGF = {0};//协议配置结构体

int _tmain(int argc, _TCHAR* argv[])
{
	//初始化接口参数
	initApiParam();
	//打卡板卡
	CHR34xxx_OpenCard();
	//复位板卡
	CHR34xxx_ResetCard();
	//打印SN号
	printf("SN:%X\n",stDevParInfo.dwSN);
	//初始化发送buf
	if (!m_recvCfg.ASYN_RecvMode)//透明模式
	{
		dwLen = 10;//发送长度
		for (int i=0;i<dwLen;i++)
		{
			TxBuf[i] = i+0xA0;
		}
	}
	else//协议模式
	{
		dwLen = 7;//发送长度
		TxBuf[0] = 0xa1;
		TxBuf[1] = 0xa2;
		TxBuf[2] = 0x03;
		TxBuf[3] = 0x11;
		TxBuf[4] = 0x22;
		TxBuf[5] = 0x33;
		TxBuf[6] = 0x00;
	}
	//停止发送
	CHR34xxx_StopSend(ChNum);
	printf("按任意键停止发送\n");
	while(!kbhit())
	{
		if (!m_sendCfg.SendMode)//若为普通发送则发送一次数据
		{
			//发送数据
			CHR34xxx_StartSend(ChNum,ChWorkMode,&m_recvCfg,&m_sendCfg,&m_ptCGF,ASYN_WordGaP,dwLen,TxBuf);
		}
		Sleep(1000);
	}
	//关闭板卡
	CHR34xxx_CloseCard();
	return 0;
}
//初始化接口参数
void initApiParam()
{
	//接收配置参数初始化
	m_recvCfg.BaudRate = 115200;//波特率 异步RS422/ 485：2400bps ~1843200bps、异步RS232：2400bps ~115200bps
	m_recvCfg.Parity = 0;//校验位(0:无校验,1:奇校验,2:偶校验)
	m_recvCfg.StopNum = 0;//停止位(0:1位停止位,1:1.5位停止位,2:2位停止位)
	m_recvCfg.DataNum = 8;//数据位(5~8位)
	m_recvCfg.ASYN_RecvMode = 0;//异步接收模式选择(0:透明模式，1:协议模式)
	m_recvCfg.IntDeepth = 5;//中断深度
	m_recvCfg.RecvIntEn = 0;//接收中断使能(0:禁止中断,1:中断使能)
	m_recvCfg.uartMode = 2;//串口模式(0:rs232,1:rs422,2:rs485)
	m_recvCfg.RecvWord16En = 1;//接收16进制使能
	//发送配置参数初始化
	m_sendCfg.SendMode = 0;//发送模式(0:普通,1:定时)
	m_sendCfg.SendWord16En = 1;//发送16进制格式使能
	m_sendCfg.FrmGap = 100000;//发送帧间隔(单位:us)
	//协议配置
	//异步协议
	m_ptCGF.asyn_frame.HDR = 0xA1;//帧头头
	m_ptCGF.asyn_frame.EDR = 0xA2;//帧头尾
	m_ptCGF.asyn_frame.TailA = 0xB1;//帧尾头
	m_ptCGF.asyn_frame.TailB = 0xB2;//帧尾尾
	m_ptCGF.asyn_frame.LENR = 3;//帧长度
	m_ptCGF.asyn_frame.pt_num = 0;//协议号(0~12)
	m_ptCGF.asyn_frame.SumCheckEN = 0;//校验和使能(0:禁止,1:使能)
	m_ptCGF.asyn_frame.HeadIncluded = 0;//值为1时，表示校验和包含帧起始符，值为0时，表示校验和不包含帧起始符
	//同步协议
	m_ptCGF.sync_frame.HR[0] = 0xA1;
	m_ptCGF.sync_frame.HR[1] = 0xA2;
	m_ptCGF.sync_frame.HR[2] = 0xA3;
	m_ptCGF.sync_frame.HR[3] = 0xA4;
	m_ptCGF.sync_frame.ER[0] = 0xB1;
	m_ptCGF.sync_frame.ER[1] = 0xB2;
	m_ptCGF.sync_frame.ER[2] = 0xB3;
	m_ptCGF.sync_frame.ER[3] = 0xB4;
	m_ptCGF.sync_frame.FrameIDCnt = 4;//帧ID数量(0~4)
	m_ptCGF.sync_frame.FrameIDOrder = 0;//帧ID顺序(0:先高后低,1:先低后高)
	m_ptCGF.sync_frame.FrameIDLocation = 3;//帧ID位置
	m_ptCGF.sync_frame.LocationAddress = 0;//本地地址
	m_ptCGF.sync_frame.SYNCWordCnt = 4;//同步字数量
	m_ptCGF.sync_frame.CRCInitVal = 1;//CRC初始值
	m_ptCGF.sync_frame.CRCOrder = 0;//CRC顺序(0:低位在前,1:高位在前)
	m_ptCGF.sync_frame.ErrFrameEn = 0;//错帧使能(0:禁止,1使能)
	m_ptCGF.sync_frame.SendEdge = 0;//发送边沿(0:下降沿,1:上升沿)
	m_ptCGF.sync_frame.RecvEdge = 1;//接收边沿(0:下降沿,1:上升沿)
	m_ptCGF.sync_frame.RecvMode = 0;//接收模式(0:普通模式,1:监听模式)
	m_ptCGF.sync_frame.AddressTesting = 0;//地址检测(0:禁止,1使能)
	m_ptCGF.sync_frame.CRCTesting = 0;//CRC校验检测(0:禁止,1使能)
	m_ptCGF.sync_frame.SYNCWordTesting = 0;//同步字检测(0:禁止,1使能)
	m_ptCGF.sync_frame.CodeErrTesting = 0;//编码错误检测(0:禁止,1使能)
	m_ptCGF.sync_frame.lackCntTesting = 0;//少数错误检测(0:禁止,1使能)
}

/***********************信号响应***********************/
//打开板卡响应
void CHR34xxx_OpenCard()
{
	//打开板卡
	if(!CHR34XXX_OpenDev(devId))
	{
		printf("Error:CHR34XXX_OpenDev\n");
		system("pause");
	}
	//获取板卡信息
	if(!CHR34XXX_GetDevParInfo(devId,&stDevParInfo))
	{
		printf("Error:CHR34XXX_GetDevParInfo\n");
		system("pause");
	}
	//获取设备总线信息
	if(!CHR34XXX_GetDevBusInfo(devId,&stDevBusInfo))
	{
		printf("Error:CHR34XXX_GetDevBusInfo\n");
		system("pause");
	}
}
//开始发送响应
void CHR34xxx_StartSend(BYTE ChNum,BYTE ChWorkMode,RecvCfg* m_recvCfg,SendCfg* m_sendCfg,ptCGF* m_ptCGF,DWORD ASYN_WordGaP,DWORD dwLen,BYTE* TxBuf)
{
	//公共串口配置
	CHR34xxx_send_comm_uartCgf(ChNum,ChWorkMode,m_recvCfg);
	if(!ChWorkMode)//异步模式
	{
		//异步串口配置
		CHR34xxx_asyn_uartSendCfg(ChNum,m_sendCfg,ASYN_WordGaP);
	}
	else//同步模式
	{
		//同步串口配置
		CHR34xxx_sync_uartSendCfg(ChNum,m_sendCfg,m_ptCGF);
	}
	// /////////////////////串口数据发送///////////////////
	CHR34xxx_uart_DataSend(ChNum,m_sendCfg,ChWorkMode,dwLen,TxBuf);
}

//停止发送响应
void CHR34xxx_StopSend(BYTE ChNum)
{
	//停止定时发送
	if(!CHR34XXX_TxCh_Stop(devId,ChNum))
	{
		printf("error:CHR34XXX_TxCh_Stop\n");
		system("pause");
	}
}

//复位响应
void CHR34xxx_ResetCard()
{
	if(!CHR34XXX_ResetDev(devId))
	{
		printf("Error:CHR34XXX_ResetDev\n");
		system("pause");
	}
	if(!CHR34XXX_RxInt_CreateEvent(devId,&hEvt))
	{
		printf("Error:CHR34XXX_RxInt_CreateEvent\n");
		//system("pause");
	}
}

//关闭响应
void CHR34xxx_CloseCard()
{
	if(hEvt != NULL)
		CHR34XXX_RxInt_CloseEvent(devId,hEvt);
	if(!CHR34XXX_ResetDev (devId))
	{
		printf("Error:CHR34XXX_ResetDev\n");
		system("pause");
	}
	if(!CHR34XXX_CloseDev(devId))
	{
		printf("Error:CHR34XXX_CloseDev\n");
		system("pause");
	}
}

/***********************板卡配置***********************/
//发送公共配置
void CHR34xxx_send_comm_uartCgf(BYTE ChNum,BYTE ChWorkMode,RecvCfg* m_recvCfg)
{
	// //////////////板卡接收操作///////////////
	//设置工作类型
	if(ChNum%2 == 0)//奇数通道设置
	{
		if(!CHR34XXX_Ch_SetType(devId,ChNum+1,!ChWorkMode))
		{
			printf("error:CHR34XXX_Ch_SetType\n");
			system("pause");
		}
	}
	else
	{
		if(!CHR34XXX_Ch_SetType(devId,ChNum,!ChWorkMode))
		{
			printf("error:CHR34XXX_Ch_SetType\n");
			system("pause");
		}	
	}
	//设置串口数据传输格式
	CHRUART_DCB_ST* stRsdcb = new CHRUART_DCB_ST;
	stRsdcb->BaudRate = m_recvCfg->BaudRate;
	stRsdcb->ByteSize = m_recvCfg->DataNum;
	stRsdcb->StopBits = m_recvCfg->StopNum;
	stRsdcb->Parity = m_recvCfg->Parity;
	if(! CHR34XXX_Ch_SetCommState(devId,ChNum,stRsdcb))
	{
		printf("error:CHR34XXX_Ch_SetCommState\n");
		system("pause");
	}	
}


//异步发送配置
void CHR34xxx_asyn_uartSendCfg(BYTE ChNum,SendCfg* m_sendCfg,DWORD ASYN_WordGaP)
{
	//设置串口数据发送模式
	if(!CHR34XXX_TxCh_SetMode(devId,ChNum,m_sendCfg->SendMode))
		printf("error:CHR34XXX_TxCh_SetMode\n");
	//设置发送字间隔
	if(!CHR34XXX_Asyn_TxCh_SetWordGap(devId,ChNum,ASYN_WordGaP))
	{
		printf("error:CHR34XXX_Asyn_TxCh_SetWordGap\n");
	}
	if(m_sendCfg->SendMode == 0)//普通发送
	{

	}
	else if(m_sendCfg->SendMode == 1)//定时发送
	{
		//设置定时发送周期
		if(!CHR34XXX_TxCh_SetPeriod(devId,ChNum,m_sendCfg->FrmGap))
			printf("error:CHR34XXX_TxCh_SetPeriod\n");
	}
}
//同步串口发送配置
void CHR34xxx_sync_uartSendCfg(BYTE ChNum,SendCfg* m_sendCfg,ptCGF* m_ptCGF)
{
	//设置串口数据发送模式
	if(!CHR34XXX_TxCh_SetMode(devId,ChNum,m_sendCfg->SendMode))
		printf("error:CHR34XXX_TxCh_SetMode\n");
	//设置同步串口发送数据时钟边沿
	if(!CHR34XXX_Sync_Ch_TREdge(devId,ChNum,m_ptCGF->sync_frame.SendEdge,m_ptCGF->sync_frame.RecvEdge))
		printf("Error:CHR34XXX_Sync_Ch_TREdge\n");
	if(m_sendCfg->SendMode == 0)//普通发送
	{

	}
	else if(m_sendCfg->SendMode == 1)//定时发送
	{
		//设置定时发送周期
		if(!CHR34XXX_TxCh_SetPeriod(devId,ChNum,m_sendCfg->FrmGap))
			printf("error:CHR34XXX_TxCh_SetPeriod\n");
		// ////////////////配置发送////////////////
		//设置同步串口定时发送的帧ID
		if(!CHR34XXX_Sync_Ch_FrmId(devId,ChNum,m_ptCGF->sync_frame.FrameIDCnt,m_ptCGF->sync_frame.FrameIDLocation,m_ptCGF->sync_frame.FrameIDOrder))
		{
			printf("error:CHR34XXX_Sync_Ch_FrmId\n");
		}
	}
}







//串口数据发送相关操作
void CHR34xxx_uart_DataSend(BYTE ChNum,SendCfg* m_sendCfg,BYTE ChWorkMode,DWORD dwLen,BYTE* TxBuf)
{
	if(m_sendCfg->SendMode == 0)//普通发送
	{
		// ////////////////发送数据////////////////
		//获得fifo状态
		DWORD Statetmp = 0;
		DWORD State = CHR34XXX_TxCh_FIFOState(devId,ChNum,&Statetmp);
		if(!(State&4))//fifo不满
		{
			DWORD dwResult = 0;
			if(!CHR34XXX_TxCh_Write(devId,ChNum,dwLen,TxBuf,&dwResult))
				printf("error:CHR34XXX_TxCh_Write\n");
		}
	}
	else if(m_sendCfg->SendMode == 1)//定时发送
	{
		// ////////////////定时发送数据////////////////
		//停止定时发送
		CHR34XXX_TxCh_Stop(devId,ChNum);
		DWORD FIFOCounttmp = 0;
		if(!CHR34XXX_TxCh_FIFOCount(devId,ChNum,&FIFOCounttmp))
		{
			printf("error:CHR34XXX_TxCh_FIFOCount\n");
		}
		if(!FIFOCounttmp)
		{
			DWORD dwResult = 0;
			if(!CHR34XXX_TxCh_Write(devId,ChNum,dwLen,TxBuf,&dwResult))
				printf("error:CHR34XXX_TxCh_Write\n");
		}
		//开始定时发送
		CHR34XXX_TxCh_Start(devId,ChNum);
	}
}