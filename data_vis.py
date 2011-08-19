#
# Deals with displaying the data gathered by the Statistics class.
#

from PySFML import sf
from OpenGL.GL import *

# do this before importing pylab or pyplot
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import StringIO, Image


class DataVis():
    def __init__(self, stats):
        self.stats = stats
        self.window = sf.RenderWindow()
        self.update_ticks = 30
        self.running = False


    def init(self):
        self.window.Create(sf.VideoMode(800, 600), "sugarscape data")
        self.window.SetActive(True)
        self.window.PreserveOpenGLStates(True)
        self.resized(800, 600)
        glDisable(GL_DEPTH_TEST)

        self.tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.tex_id)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

        self.running = True
        self.current_tick = 0
        self.next_update_tick = 0


    def deinit(self):
        glDeleteTextures([self.tex_id])
        self.tex_id = 0
        self.window.Close()
        self.running = False


    def setRunning(self, running):
        if self.running == running:
            return

        self.running = running
        if self.running:
            self.init()
        else:
            self.deinit()


    def tick(self):
        self.doEvents()

        if not self.running:
            return

        self.current_tick += 1

        if self.current_tick < self.next_update_tick:
            return

        self.updateVis()
        self.next_update_tick = self.current_tick + self.update_ticks


    def updateVis(self):
        # create figure
        fig = plt.figure(figsize=(self.window.GetWidth()/100.0, self.window.GetHeight()/100.0), dpi=100)

        # create time data array
        time_start, time_end = self.stats.getTimePeriod()
        times = [i for i in range(time_start, time_end)]

        # plot data on figure
        ax = fig.add_subplot(111, xlabel="time")
        l1 = ax.plot(times, self.stats.getNumAgentsData(), label="num_agents")
        l3 = ax.plot(times, self.stats.getNumFertileData(), label="fertile")
        l4 = ax.plot(times, self.stats.getNumDeathsData(), label="num_deaths")
        l5 = ax.plot(times, self.stats.getNumBirthsData(), label="num_births")
        l6 = ax.plot(times, self.stats.getMeanVisionData(), label="mean_vision")
        l7 = ax.plot(times, self.stats.getMeanSugarMetabolismData(), label="mean_sugar_metabolism")
        l8 = ax.plot(times, self.stats.getMeanMatesData(), label="mean_mates")
        l9 = ax.plot(times, self.stats.getMeanChildrenData(), label="mean_children")

        fig.legend((l1, l3, l4, l5, l6, l7, l8, l9), ("num_agents", "num_fertile", "num_deaths", "num_births", "mean_vision", "mean_sugar_metabolism", "mean_mates", "mean_children"), "best")
        #fig.legend(l6, "mean_vision", "best")

        # save figure in IO buffer
        imgdata = StringIO.StringIO()
        fig.savefig(imgdata, format='png')
        imgdata.seek(0)  # rewind the data
        plt.clf()
        plt.close('all')

        # create OpenGL texture
        image = Image.open(imgdata)
        iw, ih = image.size
        glBindTexture(GL_TEXTURE_2D, self.tex_id)
        glTexImage2D(GL_TEXTURE_2D, 0, 3, iw, ih, 0, GL_RGBA, GL_UNSIGNED_BYTE, image.tostring("raw", "RGBA", 0, -1))

    
    def doEvents(self):
        event = sf.Event()
        while self.window.GetEvent(event):
            if event.Type in [sf.Event.KeyPressed, sf.Event.KeyReleased]:
                pass
            elif event.Type == sf.Event.Closed:
                self.setRunning(False)
            elif event.Type == sf.Event.Resized:
                self.resized(event.Size.Width, event.Size.Height)


    def draw(self):
        if not self.running:
            return

        self.window.SetActive(True)
        glLoadIdentity()
        glClear(GL_COLOR_BUFFER_BIT)

        glEnable(GL_TEXTURE_2D)
        glColor4f(1.0, 1.0, 1.0, 1.0)
        glBegin(GL_QUADS)

        glTexCoord2f(0.0, 0.0)
        glVertex3f( 0.0, 0.0,  0.0)

        glTexCoord2f(1.0, 0.0)
        glVertex3f( 1.0, 0.0,  0.0)

        glTexCoord2f(1.0, 1.0)
        glVertex3f( 1.0,  1.0,  0.0)

        glTexCoord2f(0.0, 1.0)
        glVertex3f( 0.0,  1.0,  0.0)

        glEnd()

        # swap buffers
        self.window.Display()


    def draw2(self):
        if not self.running:
            return

        self.window.SetActive(True)
        glLoadIdentity()
        glClear(GL_COLOR_BUFFER_BIT)

        data = [
            self.stats.getNumAgentsData(), 
            self.stats.getNumFertileData(),
            self.stats.getNumDeathsData(), 
            self.stats.getNumBirthsData(), 
            self.stats.getMeanVisionData(),
            self.stats.getMeanSugarMetabolismData(),
            self.stats.getMeanMatesData(), 
            self.stats.getMeanChildrenData(),
        ]

        max_value = 0
        for d in data:
            for datum in d:
                max_value = max(datum, max_value)

        glColor3f(1.0, 1.0, 1.0)
        for d in data:
            glBegin(GL_LINE_STRIP)
            for x,v in enumerate(d):
                glVertex2f(x/100.0, v/float(max_value))
            glEnd()

        # swap buffers
        self.window.Display()




    def resized(self, width, height):
        self.window.SetView(sf.View(sf.FloatRect(0, 0, width, height)))

        self.window.SetActive(True)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, 1, 0, 1, -1, 1)
        glViewport(0, 0, width, height)
        glMatrixMode(GL_MODELVIEW)


    def bleh(self):
        if not hasattr(self, "tex_id"):
            self.tex_id = glGenTextures(1)
            fig = plt.figure()
            ax = fig.add_subplot(111)
            ax.plot([1,2,3])
            imgdata = StringIO.StringIO()
            fig.savefig(imgdata, format='png')
            imgdata.seek(0)  # rewind the data
            image = Image.open(imgdata)
            self.ix = image.size[0]
            self.iy = image.size[1]
            image = image.tostring("raw", "RGBA", 0, -1)
            glBindTexture(GL_TEXTURE_2D, self.tex_id)
            glTexImage2D(GL_TEXTURE_2D, 0, 3, self.ix, self.iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, image)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

        glEnable(GL_TEXTURE_2D)
        glColor4f(1.0, 1.0, 1.0, 1.0)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0); glVertex3f( 0.0, 0.0,  0.0)
        glTexCoord2f(1.0, 0.0); glVertex3f( self.ix, 0.0,  0.0)
        glTexCoord2f(1.0, 1.0); glVertex3f( self.ix,  self.iy,  0.0)
        glTexCoord2f(0.0, 1.0); glVertex3f( 1.0,  self.iy,  0.0)
        glEnd()


