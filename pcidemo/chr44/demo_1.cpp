#include <stdio.h>
#include <stdlib.h>
#include <conio.h>
#include <windows.h>
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
	//复位板卡
	if(0 != CHR44X02_ResetDev(hDev))
	{
		printf("CHR44X02_ResetDev-error!\n");
		goto ENDS;
	}

	//printf("press any key to end!\n");
	BYTE status  = 0;    
	while(!kbhit())
	{
		for(bti = 0;bti<24;bti++)
		{
			CHR44X02_IO_GetInputStatus(hDev,bti,&status);  //获取通道状态
			printf("ch[%d] = %d\n",bti,status);            //电源/电源断：0表示电源断，1表示电源,  电源地/电源地断：0表示电源地断，1表示电源地
		}
		Sleep(500);
	}
	
	
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