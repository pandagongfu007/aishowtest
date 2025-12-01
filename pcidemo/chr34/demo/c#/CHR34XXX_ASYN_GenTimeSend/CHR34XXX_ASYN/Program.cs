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
            int maxChNum = 8;//最大通道数
            int devId = 0;//板卡号
            IntPtr hEvt = new IntPtr();//中断句柄
            CHR_DEVPARST stDevParInfo = new CHR_DEVPARST();//板卡信息结构体
            CHR_DEVBUSST stDevBusInfo = new CHR_DEVBUSST();//板卡总线信息结构体
            
            Byte ChNum = 1;//测试通道
            CHRUART_DCB_ST stRsdcb = new CHRUART_DCB_ST();//串口数据传输格式配置结构体
            stRsdcb.BaudRate = 115200;//波特率
            stRsdcb.ByteSize = 8;//数据位
            stRsdcb.StopBits = 0;//停止位
            stRsdcb.Parity = 0;//校验位
            
            Byte ChWorkMode = 1;//设置工作类型(0:同步模式,1:异步模式)
            Byte uartMode = 1;//设置串口工作模式(0:rs232,1:rs422,2:rs485)
            Byte ASYN_485SelfCk = 0;//设置是否开启485自检(0:禁止,1:486自检使能)
            Byte SendMode = 1;//发送模式(0:普通,1:定时)
            UInt32 ASYN_WordGaP = 8;//发送字间隔
            UInt32 FrmGap = 100000;//定时发送周期us
            
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
            ////复位板卡
            //if (CHR34XXXAPI.CHR34XXX_ResetDev(devId)==0)
            //{
            //    Console.Write("Err:CHR34XXX_ResetDev-error!\n");
            //    Console.ReadKey();
            //    return;
            //}
            //创建中断句柄
            if (CHR34XXXAPI.CHR34XXX_RxInt_CreateEvent(devId,ref hEvt)==0)
            {
                //Console.Write("Err:CHR34XXX_RxInt_CreateEvent-error!\n");
            }
            //打印SN号
            Console.Write("SN=0x");
            Console.WriteLine(stDevParInfo.dwSN.ToString("X"));
            //初始化发送buf
            UInt32 dwLen = 10;//发送长度
            Byte[] TxBuf = new Byte[256];//发送buf
            for (int i = 0; i < dwLen; i++)
            {
                TxBuf[i] = (Byte)(i + 0xA0);
            }
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
            //设置串口工作模式
            if (CHR34XXXAPI.CHR34XXX_Ch_SetMode(devId, ChNum,uartMode) == 0)
            {
                Console.Write("Err:CHR34XXX_Ch_SetMode-error!\n");
                Console.ReadKey();
                return;
            }
            //设置是否开启485自检
            if (CHR34XXXAPI.CHR34XXX_Asyn_Ch_RS485LoopBack(devId, ChNum, ASYN_485SelfCk) == 0)//开启485自检
            {
                Console.Write("Err:CHR34XXX_Asyn_Ch_RS485LoopBack-error!\n");
                Console.ReadKey();
                return;
            }
            /****************异步发送配置********************/
            //设置串口数据发送模式
            if (CHR34XXXAPI.CHR34XXX_TxCh_SetMode(devId, ChNum, SendMode) == 0)
            {
                Console.Write("Err:CHR34XXX_TxCh_SetMode-error!\n");
                Console.ReadKey();
                return;
            }
            //设置发送字间隔
            if (CHR34XXXAPI.CHR34XXX_Asyn_TxCh_SetWordGap(devId, ChNum, ASYN_WordGaP)==0)
            {
                Console.Write("Err:CHR34XXX_Asyn_TxCh_SetWordGap-error!\n");
                Console.ReadKey();
                return;
            }
            //设置定时发送周期
            if (CHR34XXXAPI.CHR34XXX_TxCh_SetPeriod(devId, ChNum,FrmGap) == 0)
            {
                Console.Write("Err:CHR34XXX_TxCh_SetPeriod-error!\n");
                Console.ReadKey();
                return;
            }
    
        /****************************开始发送***************************/
            // ////////////////定时发送数据////////////////
            //停止定时发送
            CHR34XXXAPI.CHR34XXX_TxCh_Stop(devId, ChNum);
            UInt32 FIFOCounttmp = 0;
            if (CHR34XXXAPI.CHR34XXX_TxCh_FIFOCount(devId, ChNum,ref FIFOCounttmp)==0)
            {
                Console.Write("Err:CHR34XXX_TxCh_FIFOCount-error!\n");
                Console.ReadKey();
                return;
            }
            if (FIFOCounttmp==0)
            {
                UInt32 dwResult = 0;
                if (CHR34XXXAPI.CHR34XXX_TxCh_Write(devId, ChNum, dwLen, TxBuf, ref dwResult) == 0)
                {
                    Console.Write("Err:CHR34XXX_TxCh_Write-error!\n");
                    Console.ReadKey();
                    return;
                }
            }
            //开始定时发送
            CHR34XXXAPI.CHR34XXX_TxCh_Start(devId, ChNum);

            while (_kbhit() == 0)
            {

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
