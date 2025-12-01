// CHR34X0X_demo_vs.cpp : 定义控制台应用程序的入口点。
//

#include "stdafx.h"
#include "../../Lib/CHR34XXX_lib.h"
#include <conio.h>
#define MAXCHNUM 8

void InitCard();//初始化板卡
void CardChCfg();//配置板卡通道
void ExitCard();//退出板卡
void comcfg(); // 同步串口配置
void SynChCfg(); // 同步串口接收配置
void SynChRxOp();//同步串口接收操作

int devId = 0;//板卡id
BYTE testCh0 = 3;//测试通道0
HANDLE hEvent = NULL;

int _tmain(int argc, _TCHAR* argv[])
{
	//初始化板卡
	InitCard();
	//配置板卡通道
	CardChCfg();
	// 同步串口配置
	comcfg();
	// 同步串口接收配置
	SynChCfg(); 
	printf("按任意键退出\n");
	while(!kbhit())
	{
		SynChRxOp();//同步串口接收操作
	}
	//退出板卡
	ExitCard();
	return 0;
}


void InitCard()
{
	//打开板卡
	if (!CHR34XXX_OpenDev(devId))
	{
		printf("Error:CHR34XXX_OpenDev\n");
		system("pause");
		exit(0);
	}
	//复位板卡
	if (!CHR34XXX_ResetDev(devId))
	{
		printf("Error:CHR34XXX_ResetDev\n");
		system("pause");
		exit(0);
	}
	//获取板卡设备信息
	CHR_DEVPARST stDevParInfo = {0};
	CHR34XXX_GetDevParInfo(devId,&stDevParInfo);
	printf("SN = %X\n",stDevParInfo.dwSN);//打印SN号
}

//配置板卡通道
void CardChCfg()
{
	CHR34XXX_Ch_SetType(devId,testCh0,0);   //Type:串口类型 0:同步串口  1:异步串口
	//通道模式设置
	CHR34XXX_Ch_SetMode(devId,testCh0,1);//设置为rs485 模式Mode：通道模式，0 表示 232 模式，1 表示 422 模式，2 表示 485 模式
	//配置串口(波特率等)
	CHRUART_DCB_ST stRsdcb = {0};
	stRsdcb.BaudRate = 115200;// 波特率
	stRsdcb.ByteSize = 8;// 数据位
	stRsdcb.Parity = 0;// 校验位
	stRsdcb.StopBits = 0;//停止位
	CHR34XXX_Ch_SetCommState(devId,testCh0,&stRsdcb);
	//485自环使能
	CHR34XXX_Asyn_Ch_RS485LoopBack(devId,testCh0,0);//通道0 设置RS485自环使能 mode:TRUE为使能485自环 FALSE为禁止485自环
	
}

//退出板卡
void ExitCard()
{
	//停止发送
	CHR34XXX_TxCh_Stop(devId,testCh0);
	//停止接收
	CHR34XXX_RxCh_Stop(devId,testCh0);
	//关闭接收中断事件﹤接收中断使能时选择﹥
	if (hEvent != NULL)
		CHR34XXX_RxInt_CloseEvent(devId,hEvent);
	//复位板卡
	if (!CHR34XXX_ResetDev(devId))
	{
		printf("Error:CHR34XXX_ResetDev\n");
		system("pause");
		exit(0);
	}
	//关闭板卡
	if (!CHR34XXX_CloseDev(devId))
	{
		printf("Error:CHR34XXX_CloseDev\n");
		system("pause");
		exit(0);
	}
}


void SynChCfg() // 同步串口接收配置
{
	CHR34XXX_FM_Ch_RxMode(devId,testCh0,0);         //接收模式 0:FIFO 1:刷新
	CHR34XXX_FM_Ch_TimeOutEn(devId,testCh0,0);     //超时丢帧使能
	CHR34XXX_FM_Ch_SetTimeOut(devId,testCh0,0);   //超时丢帧时间
	CHR34XXX_RxInt_Enable(devId,testCh0,0);   //接收中断使能
	CHR34XXX_RxInt_CreateEvent(devId, &hEvent);
	CHR34XXX_RxCh_ClearFIFO(devId, testCh0); //清空0通道发送fifo
	CHR34XXX_RxCh_Start(devId, testCh0); //开始接收
}


void SynChRxOp()//同步串口接收操作
{
	DWORD FrmCnt = 0;
	DWORD dwResult = 0;
	BYTE Rxbuf[256] = {0};
	CHR34XXX_FM_Ch_RxFrmCount(devId,testCh0,&FrmCnt); //缓冲区帧数量
	if(FrmCnt>0)//帧数量大于0
	{
		CHR34XXX_FM_Ch_ReadFrm(devId,testCh0,256,Rxbuf,&dwResult);
		//打印接收数据
		for (int i=0;i<dwResult;i++)
		{
			printf("RevData = %x\n",Rxbuf[i]);
		}
	}
}
void comcfg()
{
	BYTE LocalAddr = 03;//本地地址
	CHR34XXX_Sync_Ch_LocalAddr(devId,testCh0,LocalAddr);   //同步串口本地地址

	BYTE CrcVal = 1;//CRC初始值
	BYTE CrcOrder = 0;//CRC顺序(0:低位在前,1:高位在前)
	CHR34XXX_Sync_Ch_SetCrc(devId,testCh0,CrcVal,CrcOrder);   //同步串口CRC设置 

	WORD IdCnt = 4; // 帧ID数量(0~4)
	WORD IdPos = 3; //帧ID位置
	WORD IdOrder = 0;//帧ID顺序(0:先高后低,1:先低后高)
	CHR34XXX_Sync_Ch_FrmId(devId,testCh0,IdCnt,IdPos,IdOrder);  //设置同步帧ID

	CHR34XXX_Sync_Ch_MonitorEn(devId,testCh0,0);        //同步串口监听模式使能

	BYTE TxEdge = 0;
	BYTE RxEdge = 1;
	CHR34XXX_Sync_Ch_TREdge(devId,testCh0,TxEdge, RxEdge);   //设置同步串口时钟边沿(接收时钟边沿和发送时钟边沿必须不同)

	CHRUART_SYNC_WORD_ST stSyncWord = {0};
	stSyncWord.FHeader[0] = 0xa1;
	stSyncWord.FHeader[1] = 0xa2;
	stSyncWord.FHeader[2] = 0xa3;
	stSyncWord.FHeader[3] = 0xa4;
	stSyncWord.FTail[0] = 0xb1;
	stSyncWord.FTail[1] = 0xb2;
	stSyncWord.FTail[2] = 0xb3;
	stSyncWord.FTail[3] = 0xb4;
	stSyncWord.WordCnt = 4;
	CHR34XXX_Sync_Ch_SetSyncWord(devId,testCh0,&stSyncWord);   //设置同步字

	CHRUART_SYNC_ERRCHECK_ST stErrCheck;
	stErrCheck.AddrCheck = 0;
	stErrCheck.CodeCheck = 0;
	stErrCheck.CrcCheck = 0;
	stErrCheck.ErrCheckEn = 0;
	stErrCheck.LoseCheck = 0;
	stErrCheck.WordCheck = 0;
	CHR34XXX_Sync_Ch_SetErrCheck(devId,testCh0,&stErrCheck);  //同步串口接收错误检测

	BYTE CrcType = 0000;
	CHR34XXX_Sync_Ch_SetCrcType(devId,testCh0,CrcType,0);//设置CRC类型（新卡)
}