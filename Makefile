
obj-m += seg_driver.o gpio_down_driver.o red_driver.o green_driver.o
KDIR = ~/working/kernel
RESULT = term
SRC = $(RESULT).c
CCC = gcc



all:
	make -C $(KDIR) M=$(PWD) modules
	$(CCC) -o $(RESULT) $(SRC)

clean:
	make -C $(KDIR) M=$(PWD) clean
	rm -f $(RESULT)
