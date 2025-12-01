// CHR34X0X_demo_vs.cpp : 定义控制台应用程序的入口点。
//

#include "stdafx.h"
#include "../../Lib/CHR34XXX_lib.h"
#include <conio.h>
#define MAXCHNUM 8

//接口声明

void InitCard();//初始化板卡
void CardChCfg();//配置板卡通道
void comcfg(); // 同步串口配置
void ExitCard();//退出板卡
void SynSend();//同步发送配置
void SynSendOp(); // 同步发送操作


int devId = 0;//板卡id
BYTE testCh0 = 1;//测试通道1
HANDLE hEvent = NULL;
BYTE TxBuf[256] = {03,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0a};


int _tmain(int argc, _TCHAR* argv[])
{
	//初始化板卡
	InitCard();
	//配置板卡通道
	CardChCfg();
	//同步串口配置
	comcfg();
	//同步发送配置
	SynSend();
	// 同步发送操作
	SynSendOp();
	printf("定时发送开始,按任意键退出\n");
	system("pause");
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
	//if (!CHR34XXX_ResetDev(devId))
	//{
	//	printf("Error:CHR34XXX_ResetDev\n");
	//	system("pause");
	//	exit(0);
	//}
	//获取板卡设备信息
	CHR_DEVPARST stDevParInfo = {0};//设备参数信息结构
	CHR34XXX_GetDevParInfo(devId,&stDevParInfo);
	printf("SN = %X\n",stDevParInfo.dwSN);//打印SN号
}

//配置板卡通道
void CardChCfg()
{
	CHR34XXX_Ch_SetType(devId,testCh0,0);   //Type:串口类型 0:同步串口  1:异步串口
	//通道模式设置
	CHR34XXX_Ch_SetMode(devId,testCh0,1);//设置为rs422模式
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
void comcfg()
{
	BYTE LocalAddr = 01;//本地地址
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
void SynSend()//同步定时发送配置
{
	CHR34XXX_FM_Ch_TimeOutEn(devId,testCh0,0);     //超时丢帧使能
	CHR34XXX_FM_Ch_SetTimeOut(devId,testCh0,0);   //超时丢帧时间
		//设置发送模式
	CHR34XXX_TxCh_SetMode(devId,testCh0,1);//发送模式mode 0：单次发送，1：定时发送
	//设置定时发送周期
	CHR34XXX_TxCh_SetPeriod(devId,testCh0,50000);//period 定时发送周期，单位为10us
	CHR34XXX_Asyn_TxCh_SetWordGap(devId,testCh0,0);//设置发送字间隔 gap（仅适用于异步串口）

}
void SynSendOp() // 同步发送操作
{

	DWORD Length = 10;//发送数据量
	//BYTE Buffer[256] = {0};//发送buf
	DWORD Writte = 0;//实际发送的字节数
	//for (int i=0;i<Length;i++)
	//{
	//	Buffer[i] = i+0xA0;
	//}
	//读取发送FIFO的状态
	DWORD State = 0;
	CHR34XXX_TxCh_FIFOState(devId,testCh0,&State);//State：发送缓冲区状态
	//若发送FIFO不满，则发送数据
	CHR34XXX_TxCh_Write(devId,testCh0,Length,TxBuf,&Writte);//Length： 待发送数据的大小，不能为 0 Buffer：待发送数据 Written：实际写入的数据
	//开始数据的发送
	CHR34XXX_TxCh_Start(devId,testCh0);

}