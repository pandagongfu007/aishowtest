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

	BYTE status  = 0;    
	for(bti=0;bti<24;bti++)
	{
		status = bti%2;    //偶数通道输出低，奇数通道输出高
		CHR44X02_IO_SetOutputStatus(hDev,bti,status);
	}
	
	printf("press any key to end!\n");
	while(!kbhit())
	{
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