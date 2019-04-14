#encoding:utf-8
def cross(alist,stdvalue):
    # crosscount = 0
    # crosslist = []
    flag = False

    if len(alist)>1:
        if alist[-2]<=stdvalue and alist[-1]>stdvalue:

            flag = True

    return flag

    #     for i in range(len(alist)):
    #         if alist[i-1]<stdvalue and alist[i]>stdvalue:
    #             crosscount+=1
    #             crosslist.append((i,alist[i]))
    #
    # return crosslist

def crossdown(alist,stdvalue):
    crosscount = 0
    crosslist = []
    flag = False
    if len(alist)>1:

        if alist[-2] >= stdvalue and alist[-1] < stdvalue:
            flag = True
    #
    #     for i in range(len(alist)):
    #         if alist[i-1]>stdvalue and alist[i]<stdvalue:
    #             crosscount+=1
    #             crosslist.append((i,alist[i]))
    #
    # return crosslist
        return flag



if __name__ == "__main__":
    testlist = []
    for i in open(r"N:\pqctpsimnow\dev\ticks\rb18005\20180302_tick.txt",'rb'):
        testlist.append(float(i.split(',')[1]))
    print(len(testlist))



    # for i in testlist:
    #     if float(i)<4012:
    #         print i
    # testlist=[1,2,3,5,6,3,2,4,7,3,7,3,2]
    stdv= 4012
    resultlist = crossdown(testlist,stdv)
    print(resultlist)