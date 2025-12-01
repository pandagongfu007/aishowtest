// CHR34X0X_demo_vs.cpp : 定义控制台应用程序的入口点。
//

#include "stdafx.h"
#include "../../Lib/CHR34XXX_lib.h"
#include <conio.h>
#define MAXCHNUM 8

void InitCard();//初始化板卡
void CardChCfg();//配置板卡通道
void ExitCard();//退出板卡

void CardChRxCfg();//通道普通接收配置
void CardChRxOp();//通道普通接收操作

int devId = 0;//板卡id
BYTE testCh0 = 2;//测试通道0
HANDLE hEvent = NULL;

int _tmain(int argc, _TCHAR* argv[])
{
	//初始化板卡
	InitCard();
	//配置板卡通道
	CardChCfg();
	//通道普通接收配置
	CardChRxCfg();
	printf("按任意键退出\n");
	while(!kbhit())
	{
		//普通接收操作
		CardChRxOp();
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

//通道普通接收配置
void CardChRxCfg()
{
	CHR34XXX_RxCh_ClearOFFlag(devId, testCh0);  //清空缓冲区溢出标记
	CHR34XXX_RxCh_ClearFIFO(devId, testCh0); //清空0通道发送fifo
	CHR34XXX_Asyn_RxCh_SetMode(devId, testCh0, 0);  //Mode接收模式 0:透明接收  1:协议接收（仅适用于普通串口）
	CHR34XXX_RxInt_Enable(devId, testCh0, 0);   //Enable接收中断使能 0:不使能中断接收模式 1：使能中断接收模式
	CHR34XXX_Asyn_RxCh_IntDepth(devId, testCh0, 0); //Depth:接收中断触发深度
	CHR34XXX_RxCh_Start(devId, testCh0); //开始接收
}

//普通接收操作
void CardChRxOp()
{
	BYTE Buffer[65535] = {0};//接收buf
	DWORD Returned = 0;//实际接收的数据量
	//读取接收FIFO数据量
	DWORD count = 0;
	CHR34XXX_Asyn_RxCh_FIFOCount(devId,testCh0,&count); //Count：接收缓冲区数据量
	//若接收FIFO的数据量不为0，则可读取数据
	if (count > 0)
	{
		//读接收fifo数据
		CHR34XXX_Asyn_RxCh_Read(devId,testCh0,count,Buffer,&Returned);//count：待读取的数据量 Buffer：存放接收到的数据 Returned：实际读取到的数据量
		//打印接收到的数据
		for (int i=0;i<Returned;i++)
		{
			printf("%X ",Buffer[i]);
		}
	}
}