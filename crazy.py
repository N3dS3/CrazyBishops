from itertools import product
from random import choices
from math import comb
from time import sleep
import tkinter

HOUNDS = -1
FOX = 1

n = 4

human = HOUNDS #0, HOUNDS, or FOX
pov = HOUNDS

cells = [coord for coord in product(range(2*n), repeat = 2) if sum(coord)%2]
shounds = {(2*n-1,2*i) for i in range(n)}

arial24 = ('Arial',24)

brazen = 0.9
temperature = 0.4
assert 0 < brazen <= 1
assert 0 < temperature <= 1

cell_size = 80

def defenses():
    '''all arrangements of four bishops'''
    def combs(within, num):
        if not num:
            yield []
        for i in range(within):
            for defense in combs(i, num - 1):
                yield [cells[i]] + defense
    yield from combs(len(cells), n)

def states():
    '''all game states'''
    for hounds in defenses():
        foxes=[fox for fox in cells if fox not in hounds]
        for fox in foxes:
            yield hounds,fox
        for fox in foxes:
            yield fox,hounds

def cindex(cell):
    '''the index of a cell'''
    return n*cell[0]+cell[1]//2
def dindex(defense):
    '''the index of an arrangement of four bishops'''
    return sum(comb(cindex(c),i+1) for i,c in enumerate(sorted(defense)))
def foxturnal(state):
    '''is it night?'''
    return isinstance(state[0],tuple)
def sindex(state):
    '''the index of a game state'''
    index=foxturnal(state)
    fox,hounds=state if index else reversed(state)
    index+=2*dindex(hounds)
    index*=2*n**2-n
    index+=cindex(fox)
    for hound in hounds:
        index-=(hound<fox)
    return index

def legal(cell):
    '''is cell is within range?'''
    return 0<=cell[0]<2*n and 0<=cell[1]<2*n
def moves(state):
    '''returns all moves from a given gamestate'''
    if foxturnal(state):
        fox,hounds=state
        for scan in product((-1,1),repeat=2):
            f=fox
            while True:
                f=f[0]+scan[0],f[1]+scan[1]
                if legal(f) and f not in hounds:
                    yield hounds,f
                else:
                    break
    else:
        hounds,fox=state
        unordered=set(hounds)
        for hound in hounds:
            for scan in product((-1,),(-1,1)):
                h=hound
                others=unordered-{hound}
                while True:
                    h=h[0]+scan[0],h[1]+scan[1]
                    if legal(h) and h!=fox and h not in hounds:
                        yield fox,others|{h}
                    else:
                        break
filename=f'crazyb{2*n}_{brazen}.txt'
try:
    with open(filename,'r') as data:
        l=[float(e) for e in data.readline().split()]
        data.close()
except FileNotFoundError:
    N = 2*(n+1)*comb(2*n**2,n+1)
    l=[None]*N
    c=0
    print('computing...')
    for index, state in enumerate(states()):
        m=[l[sindex(option)] for option in moves(state)]
        if not m:
            l[index] = -1
        else:
            negs = [i for i in m if i < 0]
            l[index] = -brazen*(sum(negs) if negs else 1/(sum([1/i for i in m])))
        c+=1
        if not c%(N//10):
            print('%3d%% loaded...'%(10*c//(N//10),))
    with open(filename,'w') as data:
        data.write(' '.join(str(e) for e in l))
        data.close()
        print('data saved'+'\n'*3)

def strategic_sample(m):
    good = [option for option in m if l[sindex(option)]<0]
    if good:
        m = good
        sanity = -1
    else:
        sanity = 1
    return choices(m, weights = [(sanity*l[sindex(option)])**(-1/temperature) for option in m])[0]

def move(state):
    '''random optimal move'''
    return strategic_sample(list(moves(state)))

def sconfig():
    return strategic_sample([(scell,shounds) for scell in cells[:-n]])

def label(cell):
    '''chess name for cell'''
    return ''.join(label[i] for label,i in zip(['12345678','hgfedcba'],cell))
def transcribe(state,reply):
    '''chess name for move'''
    if foxturnal(state):
        name='\t'+label(reply[1])
    else:
        name='\n'+'>-'.join(label(hound) for hound in sorted(state[0]^reply[1]))
    return ''.join(reversed(name))

class Cell(tkinter.Canvas):
    '''cell of the display'''
    def __init__(self,master,r,c,out=False):
        self.defaultBG=('blanched almond','#F1AA67')[(r+c)%2 or out]
        tkinter.Canvas.__init__(self,master,width=80,height=80,bd=0,\
                               highlightthickness=0,bg=self.defaultBG)
        self.out=out
        self.master,self.coords=master,(r,c)
        if not out:
            if pov>0:
                r=2*n-1-r
                c=2*n-1-c
            self.grid(row=r,column=c)
        self.bind('<Button-1>',lambda event:master.clicked(self,True))
        self.bind('<Button-2>',lambda event:master.clicked(self,False))
        self.bind('<Button-3>',lambda event:master.clicked(self,False))
    def reset(self,config):
        self.player=None
        if self.coords in config[1]:
            self.player=HOUNDS
        elif self.coords == config[0]:
            self.player=FOX
        self.draw()
    def draw(self):
        if self.player:
            s=self.master
            if self.out:
                s=s.master
            self.create_image(cell_size/2,cell_size/2,image=[None,s.fox,s.hound][self.player])
class MessageBox(tkinter.Frame):
    '''game status and instructions'''
    def __init__(self,master):
        tkinter.Frame.__init__(self,master,bg='black')
        self.master=master
        self.grid(row=2*n,column=0,columnspan=2*n)
        self.piece=Cell(self,0,0,True)
        self.piece.grid(row=0,column=0)
        self.textbox=tkinter.Label(self,fg='white',bg='black',font=arial24)
        self.textbox.grid(row=0,column=2)
        self.update()
    def update(self):
        for drawing in self.piece.find_all():
            self.piece.delete(drawing)
        self.piece.player=self.master.winner or self.master.player
        self.piece.draw()
        if self.master.winner:
            self.textbox['text']=' wins!'
        else:
            self.textbox['text']=', make your move.'
class Board(tkinter.Frame):
    '''the full display'''
    def __init__(self,master,):
        tkinter.Frame.__init__(self,master,bg='black')
        self.grid()
        self.hound=tkinter.PhotoImage(file='hound.png')
        self.fox=tkinter.PhotoImage(file='fox.png')
        self.cells=[[Cell(self,row,column) for column in range(2*n)]\
                    for row in range(2*n)]
        self.player,self.winner=HOUNDS,None
        self.messageBox=MessageBox(self)
        self.waiting=False
        self.focus=None
        self.reset()
    def reset(self):
        self.player,self.winner=FOX,None
        self.state=sconfig()
        for row in self.cells:
            for cell in row:
                for drawing in cell.find_all():
                    cell.delete(drawing)
                cell.reset(self.state)
        self.messageBox.update()
        self.used=0
        self.control=self.mover()
        self.act()
    def act(self):
        if next(self.control):
            print('\n')
            sleep(4)
            self.reset()
    def mover(self):
        while True:
            try:
                self.reply=move(self.state)
                self.messageBox.update()
                ai=True
                if human==2*foxturnal(self.state)-1:
                    ai=False
                    self.waiting=True
                    yield False
                    self.waiting=False
                name=transcribe(self.state,self.reply)
                self.state=self.reply
            except IndexError:
                self.winner=-self.player
                self.messageBox.update()
            finally:
                self.master.update()
            if self.winner:
                break
            else:
                if ai:
                    sleep((2+human)/2)
                for row in self.cells:
                    for cell in row:
                        cell['bg']=cell.defaultBG
                        for drawing in cell.find_all():
                            cell.player=None
                            cell.delete(drawing)
                fox,hounds=foxturnal(self.state) and self.state\
                            or reversed(self.state)
                f=self.cells[fox[0]][fox[1]]
                f.player=FOX
                f.draw()
                for hound in hounds:
                    h=self.cells[hound[0]][hound[1]]
                    h.player=HOUNDS
                    h.draw()
                self.player=-self.player
                print(name,end='')
        yield True
    def clicked(self,cell,left):
        if not self.waiting:
            return
        if cell.coords in self.state[0]:
            self.focus=cell.coords
        elif not cell.out:
            if foxturnal(self.state):
                self.reply=self.state[1],cell.coords
            else:
                self.reply=self.state[1],(self.state[0]-{self.focus}).union({cell.coords})
            if self.reply in moves(self.state):
                if left:
                    self.act()

root=tkinter.Tk()
root.title('Crazy Bishops')
Board(root)
