// CHR34X0X_demo_vs.cpp : 定义控制台应用程序的入口点。
//

#include "stdafx.h"
#include "../../Lib/CHR34XXX_lib.h"
#include <conio.h>
#define MAXCHNUM 8

//接口声明
void CardChTxOnceCfg();//通道单次发送配置
void CardChTxOnceOp();//通道单次发送操作

void InitCard();//初始化板卡
void CardChCfg();//配置板卡通道
void ExitCard();//退出板卡

int devId = 0;//板卡id
BYTE testCh0 = 1;//测试通道0
HANDLE hEvent = NULL;

int _tmain(int argc, _TCHAR* argv[])
{
	//初始化板卡
	InitCard();
	//配置板卡通道
	CardChCfg();
	//通道单次发送配置
	CardChTxOnceCfg();
	printf("按任意键退出\n");
	while(!kbhit())
	{
		//通道单次发送操作
		CardChTxOnceOp();
		Sleep(500);
	}
	//退出板卡
	ExitCard();
	return 0;
}

//通道单次发送配置
void CardChTxOnceCfg()
{
	//设置发送模式
	CHR34XXX_TxCh_SetMode(devId,testCh0,0);//发送模式mode 0：单次发送，1：定时发送
	//设置定时发送周期
	CHR34XXX_TxCh_SetPeriod(devId,testCh0,50000);//period 定时发送周期，单位为10us
	CHR34XXX_Asyn_TxCh_SetWordGap(devId,testCh0,0);//设置发送字间隔 gap（仅适用于异步串口）
}

//通道单次发送操作
void CardChTxOnceOp()
{
	DWORD Length = 10;//发送数据量
	BYTE Buffer[65535] = {0};//发送buf
	DWORD Writte = 0;//实际发送的字节数
	for (int i=0;i<Length;i++)
	{
		Buffer[i] = i;
	}
	//读取发送FIFO的状态
	DWORD State = 0;//State：接收缓冲区 FIFO 状态
	CHR34XXX_TxCh_FIFOState(devId,testCh0,&State);
	//若发送FIFO不满，则发送数据
	CHR34XXX_TxCh_Write(devId,testCh0,Length,Buffer,&Writte);//Length： 待发送数据的大小 pBuffer：待发送数据 pWritten：实际写入的数据

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
	////复位板卡
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
	//通道模式设置
	CHR34XXX_Ch_SetMode(devId,testCh0,1);//设置为rs485模式
	//配置串口(波特率等)
	CHRUART_DCB_ST stRsdcb = {0};
	stRsdcb.BaudRate = 115200;// 波特率
	stRsdcb.ByteSize = 8;// 数据位
	stRsdcb.Parity = 0;// 校验位
	stRsdcb.StopBits = 0;//停止位
	CHR34XXX_Ch_SetCommState(devId,testCh0,&stRsdcb);
	//485自环使能
	CHR34XXX_Asyn_Ch_RS485LoopBack(devId,testCh0,0);//通道0 设置RS485自环使能 mode:TRUE为使能485自环 FALSE为禁止485自环
	CHR34XXX_Ch_SetType(devId,testCh0,1);   //Type:串口类型 0:同步串口  1:异步串口
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