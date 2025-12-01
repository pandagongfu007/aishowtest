#include <stdio.h>
#include <stdlib.h>
#include <conio.h>
#include <windows.h>
#include "ver_helpers_legacy.h"  
#include "Lib\CHR44X02_lib.h"




HANDLE hDev = NULL;      //板卡句柄

void main()
{
	BYTE bti=0;
	BYTE cardid;

	//打开板卡
	cardid = 0;   //板卡id
	if(0 != CHR44X02_OpenDev(&hDev,cardid))
	{
		printf("CHR44X02_OpenDev-error!\n");
		goto ENDS;
	}

	// ★ 查询 CHR44 的 DLL / Driver / FW 版本（仅 ANSI 版本，不依赖 C++11）
		//	  - dllPath 建议指向你工程里实际拷贝的 DLL 路径（比如 x64 放 Lib\\x64\\）
		//	  - 若 DLL 放在 EXE 同目录，也可写成 "CHR44X02.dll"
		{
			const char* dllNames[]	  = {"CHR44X02_GetDllVersion", "CHR44X02_GetDLLVersion", "CHR44X02_GetDllVer"};
			const char* driverNames[] = {"CHR44X02_GetDriverVersion", "CHR44X02_GetDrvVersion"};
			const char* fwNames[]	  = {"CHR44X02_GetFwVersion", "CHR44X02_GetFirmwareVersion"};
	
			QueryAndPrintDllDriverFW_A(
				"Lib\\x64\\CHR44X02.dll",  // ← 根据你的实际 DLL 位置调整
				"CHR44",
				cardid,
				dllNames,	 sizeof(dllNames)/sizeof(dllNames[0]),
				driverNames, sizeof(driverNames)/sizeof(driverNames[0]),
				fwNames,	 sizeof(fwNames)/sizeof(fwNames[0])
			);
		}

	
	//复位板卡
	if(0 != CHR44X02_ResetDev(hDev))
	{
		printf("CHR44X02_ResetDev-error!\n");
		goto ENDS;
	}

	CHR44X02_SetWorkMode( hDev,2);

	HANDLE hEvent = NULL;
	CHR44X02_TrigIn_CreateEvent(hDev, &hEvent);

	BYTE trigLine = 0;
	BYTE Edge = 3;
	if(0 != CHR44X02_TrigIn_Config( hDev, trigLine, Edge))
	{
		printf("CHR44X02_TrigIn_Config-error!\n");
		goto ENDS;
	}

	//printf("press any key to end!\n");
	BYTE status  = 0;    
	while(!kbhit())
	{
		DWORD dwst = CHR44X02_TrigIn_WaitEvent(hDev, hEvent,1000);

		CHR44X02_TrigIn_GetStatus(hDev,&status);  
		printf("trig[%d] = %d---%d\n",trigLine,status,dwst);            
		//Sleep(1);
	}
	
	CHR44X02_TrigIn_CloseEvent(hDev, hEvent);

	printf("press any key to end!\n");
	getch();
	
ENDS:
	if(hDev)
	{
		CHR44X02_ResetDev(hDev);
		CHR44X02_CloseDev(hDev);
	}
	getch();
}