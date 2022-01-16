#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <termios.h>

#include <netinet/in.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <poll.h>
#include <signal.h>
#include <arpa/inet.h>

#include <errno.h>
#include <resolv.h>
#include <pthread.h>

#include <sys/un.h>
#include <iconv.h>

static struct termios init_setting, new_setting;
char seg_num[10] = {0xc0, 0xf9, 0xa4, 0xb0, 0x99, 0x92, 0x82, 0xd8, 0x80, 0x90}; //0~9
char seg_dnum[10] = {0x40, 0x79, 0x24, 0x30, 0x19, 0x12, 0x02, 0x58, 0x00, 0x10};	//0.~9.

#define D1 0x01 //맨 왼쪽
#define D2 0x02
#define D3 0x04
#define D4 0x08	//맨 오른쪽
#define MAX_SIZE 1024
#define PORT 8080

int main(int argc, char **argv)
{


    // device 동작
    unsigned short data[4];
    int count;
    int delay_time = 5000;
	int a, b, c, d;
	int temp = 0;	
	
	float prob = 0.0;
	float threshold = 8000.0;
	int int_prob;

	char sendBuff[4];
	sendBuff[0] = 'h';
	sendBuff[1] = 'i';
	char ref_down;
	char ref_up;
	char buff1;
	char tmp1;
	char prev1;
    
	int dev_seg = open("/dev/my_segment", O_RDWR); // if you want read='O_RDONLY' write='O_WRONLY', read&write='O_RDWR'
	int dev_red = open("/dev/my_gpio_red", O_RDWR); // if you want read='O_RDONLY' write='O_WRONLY', read&write='O_RDWR'
    int dev_green = open("/dev/my_gpio_green", O_RDWR); // if you want read='O_RDONLY' write='O_WRONLY', read&write='O_RDWR'
	int dev_down = open("/dev/my_gpio_down", O_RDONLY); // if you want read='O_RDONLY' write='O_WRONLY', read&write='O_RDWR'


	if(dev_seg == -1) {
		printf("Opening was not possible!(segment)\n");
		return -1;
	}
	if(dev_red == -1) {
		printf("Opening was not possible!(red led)\n");
		return -1;
	}
   	if(dev_green == -1) {
		printf("Opening was not possible!(green led)\n");
		return -1;
	}
	if(dev_down == -1) {
		printf("Opening was not possible!(down button)\n");
		return -1;
	}

	printf("device opening was successfull!\n");
    // socket 연결부

    int sock = 0, valread;
    struct sockaddr_in serv_addr;
    char buff[MAX_SIZE];
    if((sock = socket(AF_INET, SOCK_STREAM, 0)) < 0)
    {
        printf("\n socket creation error\n");
        return -1;
    }

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(PORT);

    if(inet_pton(AF_INET, "192.168.133.149", &serv_addr.sin_addr) <= 0)
    {
        printf("\nInvalid address/ Address not supported \n");
        return -1;
    }

    if(connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0 )
    {
        printf("\nConnection Failed \n");
        return -1;
    }


	read(dev_down, &buff1, 1);
	ref_down = buff1;
	prev1 = buff1;
	tmp1 = buff1;

	while(1){

        // 버튼이 눌린다면
		read(dev_down, &buff1, 1);
		prev1 = tmp1;
		tmp1 = buff1;

		//printf("\nbuff1: %c  prev1: %c  tmp1: %c", buff1, prev1, tmp1);      
		if(prev1 != tmp1) {
			//printf("\nchange");
			if(tmp1 != ref_down) {
				ref_up = tmp1;
				write(dev_green, &ref_down, 1);
				write(dev_red, &ref_down, 1);
				//printf("\nbutton");
                send(sock, sendBuff, strlen(sendBuff), 0);
				//printf("\nterm.c: send success!");
                if(read(sock, buff, MAX_SIZE) > 0) {
					//printf("\nterm.c: read success!");
         		    prob = atof(buff);
		            //printf("%f",prob);
					int_prob = prob *10000.0;
					printf("%d", int_prob);
		            if(int_prob >= threshold )
                		write(dev_green, &ref_up, 1);
		            else
		                write(dev_red, &ref_up, 1);

        		}
			}
		}
		
        // server로부터 값을 받아온다면
        
        
        
        a = int_prob / 1000;
        b = (int_prob / 100) % 10;
        c = (int_prob / 10) % 10;
        d = int_prob % 10;

		data[0] = (seg_num[a] << 4) | D1;
		data[1] = (seg_dnum[b] << 4) | D2;
		data[2] = (seg_num[c] << 4) | D3;
		data[3] = (seg_num[d] << 4) | D4;
		

		write(dev_seg, &data[temp], 2);
		usleep(delay_time);

		temp++;
		if(temp > 3)
			temp = 0;


	}

	write(dev_seg, 0x0000, 2);
	close(dev_seg);
	close(dev_red);
    close(dev_green);
	close(dev_down);
	return 0;
}

