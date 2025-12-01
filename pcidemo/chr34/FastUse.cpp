// demo.cpp : 定义控制台应用程序的入口点。
//

#include "stdafx.h"
#include <windows.h>
#include "../Lib/CHR34XXX_lib.h"
#include <conio.h>


int _tmain(int argc, _TCHAR* argv[])
{
	int ret = 0;
	int devId = 0;
	ret = CHR34XXX_StartDevice(devId);   //通过自定义板卡id打开板卡设备（方式1）
	if (ret != TRUE)
	{
		printf("Error:CHR34XXX_StartDevice\n");
		system("pause");
	}
	ret = CHR34XXX_Ch_SetRsMode(devId,0,2,TRUE);   //获取串口通道的缓存状态
	if (ret != TRUE)
	{
		printf("Error:CHR34XXX_Ch_SetRsMode\n");
		system("pause");
	}

	CHRUART_DCB_ST stRsdcb = {0};
	stRsdcb.BaudRate = 4000000;
	stRsdcb.ByteSize = 8;
	stRsdcb.Parity = 0;
	stRsdcb.StopBits = 0;
	ret = CHR34XXX_Ch_SetCommState(devId,0,&stRsdcb); //配置串口(波特率、数据位、停止位、校验位)
	if (ret != TRUE)
	{
		printf("Error:CHR34XXX_Ch_SetCommState\n");
		system("pause");
	}

	CHR34XXX_CH_STATUS_ST stRsChCachStu = {0};
	BYTE RxBuf[65535] = {0};
	BYTE TxBuf[65535] = {0};
	DWORD Returned = 0;
	DWORD Written = 0;

	for (int i=0;i<10;i++)
	{
		TxBuf[i] = i;
	}

	while(!kbhit())
	{
		CHR34XXX_Ch_WriteFile(devId,0,10,TxBuf,&Written);
		Sleep(100);
		 CHR34XXX_Ch_GetFIFOStatus(devId,0,&stRsChCachStu);//获取串口通道的缓存状态
		 if(stRsChCachStu.RxFIFOCnt > 0)
		 {
			 CHR34XXX_Ch_ReadFile(devId,0,stRsChCachStu.RxFIFOCnt,RxBuf,&Returned);
			 for (int i=0;i<Returned;i++)
			 {
				 printf("%X ",RxBuf[i]);
			 }
			 printf("\n");
		 }
	}
	CHR34XXX_StopDevice(devId);   //关闭板卡设备
	return 0;
}

