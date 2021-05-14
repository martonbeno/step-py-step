from StepPyStep import *

if __name__ == "__main__":

    import time
    filename = "ja2.py"
    filename = "ja.py"

    #p = StepPyStep(filename=filename)
    p = StepPyStep()
    init_msg = p.start()
    if not init_msg['compile_success']:
        print(init_msg)
        print("fordítási idejű hiba")
        print(init_msg['error_message'])
        exit()

    print(init_msg)

    while True:
        print("várom a parancsokat")
        r = input()
        if r == "quit":
            p.kill()
            break
        #time.sleep(1)
        try:
            ret = p.request(r)
        except Exception:
            print("inkább idelennnnnnnnnnnnnnnnnnnnnnn")
        print("------RET", ret)
        if ret == "exit":
            break