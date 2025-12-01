using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Linq;
using System.Threading;
using System.Text;
using System.IO;
using System.Threading.Tasks;

namespace CHR34XXX_ASYN
{
    class Program
    {
        //导入ms库
        [DllImport("msvcrt.dll")]
        //声明函数kbhit
        public static extern int _kbhit();
        static void Main(string[] args)
        {
            int devId = 0;//板卡号
            IntPtr hEvt = new IntPtr();//中断句柄
            CHR_DEVPARST stDevParInfo = new CHR_DEVPARST();//板卡信息结构体
            CHR_DEVBUSST stDevBusInfo = new CHR_DEVBUSST();//板卡总线信息结构体
            
            Byte ChNum = 2;//测试通道
            CHRUART_DCB_ST stRsdcb = new CHRUART_DCB_ST();//串口数据传输格式配置结构体
            stRsdcb.BaudRate = 115200;//波特率
            stRsdcb.ByteSize = 8;//数据位
            stRsdcb.StopBits = 0;//停止位
            stRsdcb.Parity = 0;//校验位
            

            Byte RecvIntEn = 0;//配置中断接收(0:禁止中断,1:使能中断)
            Byte ChWorkMode = 1;//设置工作类型(0:同步模式,1:异步模式)
            Byte uartMode = 1;//设置串口工作模式(0:rs232,1:rs422,2:rs485)
            Byte ASYN_485SelfCk = 0;//设置是否开启485自检(0:禁止,1:485自检使能)
            Byte ASYN_RecvMode = 0;//设置异步接收模式(0:透明模式，1:协议模式)
            Byte PtRxMode = 0;//协议接收模式(0:FIFO接收,1:刷新接收)
            //Byte TimeOutThrowFrmEn = 0;//超时丢帧使能(0:禁止,1:使能)
            //UInt32 timeOutCnt = 0;//超时丢帧时间

            
            //打开板卡
            if (CHR34XXXAPI.CHR34XXX_OpenDev(devId)==0)
            {
                Console.Write("Err:CHR34XXX_OpenDev-error!\n");
                Console.ReadKey();
                return;
            }
            //获取板卡信息
            if (CHR34XXXAPI.CHR34XXX_GetDevParInfo(devId,ref stDevParInfo) == 0)
            {
                Console.Write("Err:CHR34XXX_GetDevParInfo-error!\n");
                Console.ReadKey();
                return;
            }
            //获取设备总线信息
            if (CHR34XXXAPI.CHR34XXX_GetDevBusInfo(devId,ref stDevBusInfo) == 0)
            {
                Console.Write("Err:CHR34XXX_GetDevBusInfo-error!\n");
                Console.ReadKey();
                return;
            }
            //复位板卡
            if (CHR34XXXAPI.CHR34XXX_ResetDev(devId) == 0)
            {
                Console.Write("Err:CHR34XXX_ResetDev-error!\n");
                Console.ReadKey();
                return;
            }
            //打印SN号
            Console.Write("SN=0x");
            Console.WriteLine(stDevParInfo.dwSN.ToString("X"));
            // //////////////板卡接收配置///////////////
	        //设置工作类型
	        if(ChNum%2 == 0)//奇数通道设置
	        {
		        if(CHR34XXXAPI.CHR34XXX_Ch_SetType(devId,(Byte)(ChNum+1),ChWorkMode)==0)
		        {
                    Console.Write("Err:CHR34XXX_Ch_SetType-error!\n");
                    Console.ReadKey();
                    return;
		        }
	        }
	        else
	        {
		        if(CHR34XXXAPI.CHR34XXX_Ch_SetType(devId,ChNum,ChWorkMode)==0)
		        {
                    Console.Write("Err:CHR34XXX_Ch_SetType-error!\n");
                    Console.ReadKey();
                    return;
		        }
	        }
	        //设置串口数据传输格式
	        if(CHR34XXXAPI.CHR34XXX_Ch_SetCommState(devId,ChNum,ref stRsdcb)==0)
	        {
                Console.Write("Err:CHR34XXX_Ch_SetType-error!\n");
                Console.ReadKey();
                return;
	        }
	        //配置中断接收
            if (CHR34XXXAPI.CHR34XXX_RxInt_Enable(devId, ChNum, RecvIntEn) == 0)
		    {
                Console.Write("Err:CHR34XXX_RxInt_Enable-error!\n");
                Console.ReadKey();
                return;
		    }
	        //清空接收缓冲区
	        if(CHR34XXXAPI.CHR34XXX_RxCh_ClearFIFO(devId,ChNum)==0)
	        {
                Console.Write("Err:CHR34XXX_RxCh_ClearFIFO-error!\n");
                Console.ReadKey();
                return;
	        }
	        //清接收缓冲区溢出标志
	        if(CHR34XXXAPI.CHR34XXX_RxCh_ClearOFFlag(devId,ChNum)==0)
	        {
                Console.Write("Err:CHR34XXX_RxCh_ClearOFFlag-error!\n");
                Console.ReadKey();
                return;
	        }
            //设置串口工作模式
            if (CHR34XXXAPI.CHR34XXX_Ch_SetMode(devId, ChNum,uartMode) == 0)
            {
                Console.Write("Err:CHR34XXX_Ch_SetMode-error!\n");
                Console.ReadKey();
                return;
            }
            // ////////////////配置接收////////////////
            //设置是否开启485自检
            if (CHR34XXXAPI.CHR34XXX_Asyn_Ch_RS485LoopBack(devId, ChNum, ASYN_485SelfCk) == 0)//开启485自检
            {
                Console.Write("Err:CHR34XXX_Asyn_Ch_RS485LoopBack-error!\n");
                Console.ReadKey();
                return;
            }
            //设置异步接收模式(0:透明模式，1:协议模式)
            if (CHR34XXXAPI.CHR34XXX_Asyn_RxCh_SetMode(devId, ChNum,ASYN_RecvMode) == 0)
            {
                Console.Write("Err:CHR34XXX_Asyn_RxCh_SetMode-error!\n");
                Console.ReadKey();
                return;
            }
            //设置接收FIFO模式
            if (CHR34XXXAPI.CHR34XXX_FM_Ch_RxMode(devId, ChNum,PtRxMode) == 0)
            {
                Console.Write("Err:CHR34XXX_FM_Ch_RxMode-error!\n");
                Console.ReadKey();
                return;
            }

            //接收使能
            if (CHR34XXXAPI.CHR34XXX_RxCh_Start(devId, ChNum) == 0)
            {
                Console.Write("Err:CHR34XXX_RxCh_Start-error!\n");
                Console.ReadKey();
                return;
            }

            while (_kbhit() == 0)
            {
                //接收数据
                UInt32 RxResult = 0;//实际接收的数据
                Byte[] Rxbuf = new Byte[65535];//接收buf

                // 中断有效，需要读取数据
                UInt32 Count = 0;
                if (CHR34XXXAPI.CHR34XXX_Asyn_RxCh_FIFOCount(devId, ChNum, ref Count) == 0)
                {
                    Console.Write("Err:CHR34XXX_Asyn_RxCh_FIFOCount-error!\n");
                    Console.ReadKey();
                    return;
                }
                if (Count > 0)
                {
                    if (CHR34XXXAPI.CHR34XXX_Asyn_RxCh_Read(devId, ChNum, Count, Rxbuf, ref RxResult) == 0)
                    {
                        Console.Write("Err:CHR34XXX_Asyn_RxCh_Read-error!\n");
                        Console.ReadKey();
                        return;
                    }

                    //打印接收数据
                    for (int i = 0; i < RxResult; i++)
                    {
                        Console.Write("Data=0x");
                        Console.WriteLine(Rxbuf[i].ToString("X02"));
                    }
                }
            }

            //关闭板卡
            if (hEvt != null)
                CHR34XXXAPI.CHR34XXX_RxInt_CloseEvent(devId, hEvt);
            if (CHR34XXXAPI.CHR34XXX_ResetDev(devId)==0)
            {
                Console.Write("Err:CHR34XXX_ResetDev-error!\n");
                Console.ReadKey();
                return;
            }
            if (CHR34XXXAPI.CHR34XXX_CloseDev(devId)==0)
            {
                Console.Write("Err:CHR34XXX_CloseDev-error!\n");
                Console.ReadKey();
                return;
            }
        }
    }
}
