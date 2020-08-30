from threading import Thread
import time

# copy file
def copy_file(start_time, file_name, new_file_name):

    print_copy_start(start_time, file_name, new_file_name)

    src = './' + file_name
    dst = './' + new_file_name
        
    fsrc = open(src, 'rb')
    fdst = open(dst, 'wb')

    length=10240

    while 1:
        buf = fsrc.read(length)
        if not buf:
            break
        fdst.write(buf)


    print_copy_complete(start_time, new_file_name)

    fsrc.close()
    fdst.close()


# write 'copy start' on log file
def print_copy_start(start_time, file_name, new_file_name):
        copy_start_time = str(float("{:.2f}".format(time.time() - start_time)))
        to_write = copy_start_time + '  Start copying  ' + file_name + '  to  ' + new_file_name + '\n'
        f.write(to_write)


# write 'copy complete' on log file
def print_copy_complete(start_time, new_file_name):
        copy_end_time = str(float("{:.2f}".format(time.time() - start_time)))
        to_write = copy_end_time + '  ' + new_file_name + '  is copied completely\n'
        f.write(to_write)


def file_input():
    file_name = input('Input the file name : ')
 
    # exit the program
    if(file_name =='exit'):
        f.close()
        exit()

    new_file_name = input('Input the new name : ')
    print()

    return file_name, new_file_name



if __name__=="__main__":

    start_time = time.time()

    f = open("log.txt", 'w')

    while 1:

        file_name, new_file_name = file_input()
        
        thread = Thread(target = copy_file, args=(start_time, file_name, new_file_name))
        
        thread.start()

    
        
