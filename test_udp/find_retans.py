import re

def countmissdata():
    counter_my = 1
    counter_custom = 1
    with open(r"C:\Users\yifeifan\Desktop\new_change.txt") as file:
        for line in file.readlines():
            reline =  re.findall("\d+",line)
            if reline[0] == '0123456789':
                if int(reline[2]) == counter_my:
                    re_counter_my = counter_my
                    counter_my += 1
                elif int(reline[2]) == re_counter_my:
                    pass
                else:
                    print('my miss data number is {}'.format(counter_my))
                    counter_my = int(reline[2])
                    counter_my += 1
                    re_counter_my = counter_my - 1
                
            elif  reline[0] == '867352040569573':
                
                if int(reline[2]) == counter_custom:
                    counter_custom += 1
                else:
                    print('custom miss data number is {}'.format(counter_custom))
                    counter_custom = int(reline[2])
                    counter_custom += 1