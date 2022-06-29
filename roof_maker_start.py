#!/usr/bin/env python
# coding=utf-8
#
# Copyright (C) [2021] [Susan Zakar], [sue.zakar@gmail.com]
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# This program for 3D papercraft will construct the pieces needed to make a roof
# for a house or other structure, as well as for dormer windows that can fit against the roof.
# There are a number of configurable options, including the size of the roof and dormers.
#
#

import inkex
import math
import copy

from inkex import PathElement, Style
from inkex.paths import Move, Line, ZoneClose, Path
from inkex.elements._groups import Group

class pathStruct(object):
    def __init__(self):
        self.id="path0000"
        self.path= Path()
        self.enclosed=False
        self.style = None
    def __str__(self):
        return self.path
    
class RNodes:
    def __init__(self,x,y):
        self.x = x
        self.y = y
################################ INSET CODE *****
class pnPoint(object):
   # This class came from https://github.com/JoJocoder/PNPOLY
    def __init__(self,p):
        self.p=p
    def __str__(self):
        return self.p
    def InPolygon(self,polygon,BoundCheck=False):
        inside=False
        if BoundCheck:
            minX=polygon[0][0]
            maxX=polygon[0][0]
            minY=polygon[0][1]
            maxY=polygon[0][1]
            for p in polygon:
                minX=min(p[0],minX)
                maxX=max(p[0],maxX)
                minY=min(p[1],minY)
                maxY=max(p[1],maxY)
            if self.p[0]<minX or self.p[0]>maxX or self.p[1]<minY or self.p[1]>maxY:
                return False
        j=len(polygon)-1
        for i in range(len(polygon)):
            if ((polygon[i][1]>self.p[1])!=(polygon[j][1]>self.p[1]) and (self.p[0]<(polygon[j][0]-polygon[i][0])*(self.p[1]-polygon[i][1])/( polygon[j][1] - polygon[i][1] ) + polygon[i][0])):
                    inside =not inside
            j=i
        return inside

class Roofmaker(inkex.EffectExtension):
    def add_arguments(self, pars):
        pars.add_argument("--usermenu")
        pars.add_argument("--unit", default="in",\
            help="Dimensional units")
        pars.add_argument("--scoretype",default="dash",\
            help="Use cut-dash scorelines or solid scorelines")        
        pars.add_argument("--isbarn",default="False",\
            help="User barn style top on roof (two angles)")
        pars.add_argument("--sides", default="12",\
            help="Dormer Top Poly Sides")
        pars.add_argument("--basewidth", type=float, default=1.0,\
            help="Dormer Width (in Dimensional Units)")
        pars.add_argument("--dormerht", type=float, default=1.5,\
            help="Dormer Height (in Dimensional Units; zero for no dormer)")
        pars.add_argument("--roof_inset", type=float, default=1.0,\
            help="Roof Inset (in Dimensional Units)")
        pars.add_argument("--roofpeak", type=float, default=2.0,\
            help="Roof Peak Height (in Dimensional Units)")
        pars.add_argument("--roofdepth", type=float, default=3.0,\
            help="Roof Base Depth (in Dimensional Units)")
        pars.add_argument("--roofwidth", type=float, default=7.0,\
            help="Roof Base Width (in Dimensional Units)")
        pars.add_argument("--chimney_ht", type=float, default=45.0,\
            help="Height above roof on peak side")
            
        pars.add_argument("--chimney_wd", type=float, default=1.0,\
            help="width of chimney")
        pars.add_argument("--chimney_depth", type=float, default=.75,\
            help="depth of chimney")        
        pars.add_argument("--off_center", type=float, default=.5,\
            help="Amount off_center from peak")        
        pars.add_argument("--shrink",type=float,default=0.67,\
            help="Reduction amount for chimney tabs and scores")             
        pars.add_argument("--isabase",default="True",\
            help="There is a base on the dormer")
        pars.add_argument("--peak_down",type=float,default=1.0,\
            help="Reduce Peak of Dormer")
        pars.add_argument("--stickout",type=float,default=0.0,\
            help="Extend base of dormer from flush with roof")
        pars.add_argument("--window_frame",type=float,default=0.125,\
            help="Relative thickness of dormer window frame")

        pars.add_argument("--bhratio",type=float,default=0.2,\
            help="Relative thickness of dormer window frame")
        pars.add_argument("--bdratio",type=float,default=0.4,\
            help="Relative thickness of dormer window frame")
        
    def insidePath(self, path, p):
        point = pnPoint((p.x, p.y))
        pverts = []
        for pnum in path:
            if pnum.letter == 'Z':
                pverts.append((path[0].x, path[0].y))
            else:
                pverts.append((pnum.x, pnum.y))
        isInside = point.InPolygon(pverts, True)
        return isInside # True if point p is inside path

    def makescore(self, pt1, pt2, dashlength):
        # Draws a dashed line of dashlength between two points
        # Dash = dashlength space followed by dashlength mark
        # if dashlength is zero, we want a solid line
        # Returns dashed line as a Path object
        apt1 = Line(0.0,0.0)
        apt2 = Line(0.0,0.0)
        ddash = Path()
        if math.isclose(dashlength, 0.0):
            
            ddash.append(Move(pt1.x,pt1.y))
            ddash.append(Line(pt2.x,pt2.y))
        else:
            if math.isclose(pt1.y, pt2.y):
                
                if pt1.x < pt2.x:
                    xcushion = pt2.x - dashlength
                    xpt = pt1.x
                    ypt = pt1.y
                else:
                    xcushion = pt1.x - dashlength
                    xpt = pt2.x
                    ypt = pt2.y
                done = False
                while not(done):
                    if (xpt + dashlength*2) <= xcushion:
                        xpt = xpt + dashlength
                        ddash.append(Move(xpt,ypt))
                        xpt = xpt + dashlength
                        ddash.append(Line(xpt,ypt))
                    else:
                        done = True
            elif math.isclose(pt1.x, pt2.x):
                
                if pt1.y < pt2.y:
                    ycushion = pt2.y - dashlength
                    xpt = pt1.x
                    ypt = pt1.y
                else:
                    ycushion = pt1.y - dashlength
                    xpt = pt2.x
                    ypt = pt2.y
                done = False
                while not(done):
                    if(ypt + dashlength*2) <= ycushion:
                        ypt = ypt + dashlength         
                        ddash.append(Move(xpt,ypt))
                        ypt = ypt + dashlength
                        ddash.append(Line(xpt,ypt))
                    else:
                        done = True
            else:
               
                if pt1.y > pt2.y:
                    apt1.x = pt1.x
                    apt1.y = pt1.y
                    apt2.x = pt2.x
                    apt2.y = pt2.y
                else:
                    apt1.x = pt2.x
                    apt1.y = pt2.y
                    apt2.x = pt1.x
                    apt2.y = pt1.y
                m = (apt1.y-apt2.y)/(apt1.x-apt2.x)
                theta = math.atan(m)
                msign = (m>0) - (m<0)
                ycushion = apt2.y + dashlength*math.sin(theta)
                xcushion = apt2.x + msign*dashlength*math.cos(theta)
                xpt = apt1.x
                ypt = apt1.y
                done = False
                while not(done):
                    nypt = ypt - dashlength*2*math.sin(theta)
                    nxpt = xpt - msign*dashlength*2*math.cos(theta)
                    if (nypt >= ycushion) and (((m<0) and (nxpt <= xcushion)) or ((m>0) and (nxpt >= xcushion))):
                        # move to end of space / beginning of mark
                        xpt = xpt - msign*dashlength*math.cos(theta)
                        ypt = ypt - msign*dashlength*math.sin(theta)
                        ddash.append(Move(xpt,ypt))
                        # draw the mark
                        xpt = xpt - msign*dashlength*math.cos(theta)
                        ypt = ypt - msign*dashlength*math.sin(theta)
                        ddash.append(Line(xpt,ypt))
                    else:
                        done = True
        return ddash

    def detectIntersect(self, x1, y1, x2, y2, x3, y3, x4, y4):
        td = (x1-x2)*(y3-y4)-(y1-y2)*(x3-x4)
        if td == 0:
            # These line segments are parallel
            return False
        t = ((x1-x3)*(y3-y4)-(y1-y3)*(x3-x4))/td
        if (0.0 <= t) and (t <= 1.0):
            return True
        else:
            return False

    def orientTab(self,pt1,pt2,height,angle,theta,orient):
        tpt1 = Line(0.0,0.0)
        tpt2 = Line(0.0,0.0)
        tpt1.x = pt1.x + orient[0]*height + orient[1]*height/math.tan(math.radians(angle))
        tpt2.x = pt2.x + orient[2]*height + orient[3]*height/math.tan(math.radians(angle))
        tpt1.y = pt1.y + orient[4]*height + orient[5]*height/math.tan(math.radians(angle))
        tpt2.y = pt2.y + orient[6]*height + orient[7]*height/math.tan(math.radians(angle))
        if not math.isclose(theta, 0.0):
            t11 = Path([Move(pt1.x,pt1.y),Line(tpt1.x, tpt1.y)])
            t12 = Path([Move(pt1.x,pt1.y),Line(tpt2.x, tpt2.y)])
            thetal1 = t11.rotate(theta, [pt1.x,pt1.y])
            thetal2 = t12.rotate(theta, [pt2.x,pt2.y])
            tpt1.x = thetal1[1].x
            tpt1.y = thetal1[1].y
            tpt2.x = thetal2[1].x
            tpt2.y = thetal2[1].y
        return tpt1,tpt2

    def makeTab(self, tpath, pt1, pt2, tabht, taba):
        # tpath - the pathstructure containing pt1 and pt2
        # pt1, pt2 - the two points where the tab will be inserted
        # tabht - the height of the tab
        # taba - the angle of the tab sides
        # returns the two tab points (Line objects) in order of closest to pt1
        tpt1 = Line(0.0,0.0)
        tpt2 = Line(0.0,0.0)
        currTabHt = tabht
        currTabAngle = taba
        testAngle = 1.0
        testHt = currTabHt * 0.001
        adjustTab = 0
        tabDone = False
        while not tabDone:
            # Let's find out the orientation of the tab
            if math.isclose(pt1.x, pt2.x):
                # It's vertical. Let's try the right side
                if pt1.y < pt2.y:
                    pnpt1,pnpt2 = self.orientTab(pt1,pt2,testHt,testAngle,0.0,[1,0,1,0,0,1,0,-1])
                    if ((not tpath.enclosed) and (self.insidePath(tpath.path, pnpt1) or self.insidePath(tpath.path, pnpt2))) or \
                       (tpath.enclosed and ((not self.insidePath(tpath.path, pnpt1)) and (not self.insidePath(tpath.path, pnpt2)))):
                        tpt1,tpt2 = self.orientTab(pt1,pt2,currTabHt,currTabAngle,0.0,[-1,0,-1,0,0,1,0,-1]) # Guessed wrong
                    else:
                        tpt1,tpt2 = self.orientTab(pt1,pt2,currTabHt,currTabAngle,0.0,[1,0,1,0,0,1,0,-1]) # Guessed right
                else: # pt2.y < pt1.y
                    pnpt1,pnpt2 = self.orientTab(pt1,pt2,testHt,testAngle,0.0,[1,0,1,0,0,-1,0,1])
                    if ((not tpath.enclosed) and (self.insidePath(tpath.path, pnpt1) or self.insidePath(tpath.path, pnpt2))) or \
                       (tpath.enclosed and ((not self.insidePath(tpath.path, pnpt1)) and (not self.insidePath(tpath.path, pnpt2)))):
                        tpt1,tpt2 = self.orientTab(pt1,pt2,currTabHt,currTabAngle,0.0,[-1,0,-1,0,0,-1,0,1]) # Guessed wrong
                    else:
                        tpt1,tpt2 = self.orientTab(pt1,pt2,currTabHt,currTabAngle,0.0,[1,0,1,0,0,-1,0,1]) # Guessed right
            elif math.isclose(pt1.y, pt2.y):
                # It's horizontal. Let's try the top
                if pt1.x < pt2.x:
                    pnpt1,pnpt2 = self.orientTab(pt1,pt2,testHt,testAngle,0.0,[0,1,0,-1,-1,0,-1,0])
                    if ((not tpath.enclosed) and (self.insidePath(tpath.path, pnpt1) or self.insidePath(tpath.path, pnpt2))) or \
                       (tpath.enclosed and ((not self.insidePath(tpath.path, pnpt1)) and (not self.insidePath(tpath.path, pnpt2)))):
                        tpt1,tpt2 = self.orientTab(pt1,pt2,currTabHt,currTabAngle,0.0,[0,1,0,-1,1,0,1,0]) # Guessed wrong
                    else:
                        tpt1,tpt2 = self.orientTab(pt1,pt2,currTabHt,currTabAngle,0.0,[0,1,0,-1,-1,0,-1,0]) # Guessed right
                else: # pt2.x < pt1.x
                    pnpt1,pnpt2 = self.orientTab(pt1,pt2,testHt,testAngle,0.0,[0,-1,0,1,-1,0,-1,0])
                    if ((not tpath.enclosed) and (self.insidePath(tpath.path, pnpt1) or self.insidePath(tpath.path, pnpt2))) or \
                       (tpath.enclosed and ((not self.insidePath(tpath.path, pnpt1)) and (not self.insidePath(tpath.path, pnpt2)))):
                        tpt1,tpt2 = self.orientTab(pt1,pt2,currTabHt,currTabAngle,0.0,[0,-1,0,1,1,0,1,0]) # Guessed wrong
                    else:
                        tpt1,tpt2 = self.orientTab(pt1,pt2,currTabHt,currTabAngle,0.0,[0,-1,0,1,-1,0,-1,0]) # Guessed right

            else: # the orientation is neither horizontal nor vertical
                # Let's get the slope of the line between the points
                # Because Inkscape's origin is in the upper-left corner,
                # a positive slope (/) will yield a negative value
                slope = (pt2.y - pt1.y)/(pt2.x - pt1.x)
                # Let's get the angle to the horizontal
                theta = math.degrees(math.atan(slope))
                # Let's construct a horizontal tab
                seglength = math.sqrt((pt1.x-pt2.x)**2 +(pt1.y-pt2.y)**2)
                if slope < 0.0:
                    if pt1.x < pt2.x:
                        pnpt1,pnpt2 = self.orientTab(pt1,pt2,testHt,testAngle,theta,[0,1,0,-1,-1,0,-1,0])
                        if ((not tpath.enclosed) and (self.insidePath(tpath.path, pnpt1) or self.insidePath(tpath.path, pnpt2))) or \
                           (tpath.enclosed and ((not self.insidePath(tpath.path, pnpt1)) and (not self.insidePath(tpath.path, pnpt2)))):
                            tpt1,tpt2 = self.orientTab(pt1,pt2,currTabHt,currTabAngle,theta,[0,1,0,-1,1,0,1,0]) # Guessed wrong
                        else:
                            tpt1,tpt2 = self.orientTab(pt1,pt2,currTabHt,currTabAngle,theta,[0,1,0,-1,-1,0,-1,0]) # Guessed right
                    else: # pt1.x > pt2.x
                        pnpt1,pnpt2 = self.orientTab(pt1,pt2,testHt,testAngle,theta,[0,-1,0,1,-1,0,-1,0])
                        if ((not tpath.enclosed) and (self.insidePath(tpath.path, pnpt1) or self.insidePath(tpath.path, pnpt2))) or \
                           (tpath.enclosed and ((not self.insidePath(tpath.path, pnpt1)) and (not self.insidePath(tpath.path, pnpt2)))):
                            tpt1,tpt2 = self.orientTab(pt1,pt2,currTabHt,currTabAngle,theta,[0,-1,0,1,1,0,1,0]) # Guessed wrong
                        else:
                            tpt1,tpt2 = self.orientTab(pt1,pt2,currTabHt,currTabAngle,theta,[0,-1,0,1,-1,0,-1,0]) # Guessed right
                else: # slope > 0.0
                    if pt1.x < pt2.x:
                        pnpt1,pnpt2 = self.orientTab(pt1,pt2,testHt,testAngle,theta,[0,1,0,-1,-1,0,-1,0])
                        if ((not tpath.enclosed) and (self.insidePath(tpath.path, pnpt1) or self.insidePath(tpath.path, pnpt2))) or \
                           (tpath.enclosed and ((not self.insidePath(tpath.path, pnpt1)) and (not self.insidePath(tpath.path, pnpt2)))):
                            tpt1,tpt2 = self.orientTab(pt1,pt2,currTabHt,currTabAngle,theta,[0,1,0,-1,1,0,1,0]) # Guessed wrong
                        else:
                            tpt1,tpt2 = self.orientTab(pt1,pt2,currTabHt,currTabAngle,theta,[0,1,0,-1,-1,0,-1,0]) # Guessed right
                    else: # pt1.x > pt2.x
                        pnpt1,pnpt2 = self.orientTab(pt1,pt2,testHt,testAngle,theta,[0,-1,0,+1,-1,0,-1,0])
                        if ((not tpath.enclosed) and (self.insidePath(tpath.path, pnpt1) or self.insidePath(tpath.path, pnpt2))) or \
                           (tpath.enclosed and ((not self.insidePath(tpath.path, pnpt1)) and (not self.insidePath(tpath.path, pnpt2)))):
                            tpt1,tpt2 = self.orientTab(pt1,pt2,currTabHt,currTabAngle,theta,[0,-1,0,1,1,0,1,0]) # Guessed wrong
                        else:
                            tpt1,tpt2 = self.orientTab(pt1,pt2,currTabHt,currTabAngle,theta,[0,-1,0,1,-1,0,-1,0]) # Guessed right
            # Check to see if any tabs intersect each other
            if self.detectIntersect(pt1.x, pt1.y, tpt1.x, tpt1.y, pt2.x, pt2.y, tpt2.x, tpt2.y):
                # Found an intersection.
                if adjustTab == 0:
                    # Try increasing the tab angle in one-degree increments
                    currTabAngle = currTabAngle + 1.0
                    if currTabAngle > 88.0: # We're not increasing the tab angle above 89 degrees
                        adjustTab = 1
                        currTabAngle = taba
                if adjustTab == 1:
                    # So, try reducing the tab height in 20% increments instead
                    currTabHt = currTabHt - tabht*0.2 # Could this lead to a zero tab_height?
                    if currTabHt <= 0.0:
                        # Give up
                        currTabHt = tabht
                        adjustTab = 2
                if adjustTab == 2:
                    tabDone = True # Just show the failure
            else:
                tabDone = True
            
        return tpt1,tpt2

    #draw SVG line segment(s) between the given (raw) points
    def drawline(self, dstr, name, parent, sstr=None):
        line_style   = {'stroke':'#000000','stroke-width':'0.25','fill':'#eeeeee'}
        if sstr == None:
            stylestr = str(inkex.Style(line_style))
        else:
            stylestr = sstr
        el = parent.add(inkex.PathElement())
        el.path = dstr
        el.style = stylestr
        el.label = name
  
    def insetPolygon(self, points, insetDist):
        # Converted from
        # public-domain code by Darel Rex Finley, 2007
        # See diagrams at http://alienryderflex.com/polygon_inset

        # points = list of clockwise path commands (e.g. [Mcmd, Lcmd, Lcmd, ...])
        # insetDist = positive inset distance
        # NOTE: To outset the polygon, provide CCW path commands or negative insetDist (not both)

        corners = len(points)
        startX = points[0].x
        startY = points[0].y
        # Polygon must have at least three corners to be inset
        if corners < 3:
            return
        # Inset the polygon
        c = points[corners-1].x
        d = points[corners-1].y
        e = points[0].x
        f = points[0].y
        for i in range(corners-1):
            a = c
            b = d
            c = e
            d = f
            e = points[i+1].x
            f = points[i+1].y
            #status, px, py = self.insetCorner(a,b,c,d,e,f,insetDist)
            status, px, py = self.insetCorner(a,b,c,d,e,f,insetDist)
            if status == 1:
                points[i].x = px
                points[i].y = py
            
        #status, px, py = self.insetCorner(c,d,e,f,startX,startY,insetDist)
        status, px, py = self.insetCorner(c,d,e,f,startX,startY,insetDist)
        if status == 1:
            points[-1].x = px
            points[-1].y = py
            
    def insetCorner(self, a,b,c,d,e,f,insetDist):
        # Converted from
        # public-domain code by Darel Rex Finley, 2007
        # Given the sequentially connected points (a,b), (c,d), and (e,f), this
        # function returns, in (C,D), a bevel-inset replacement for point (c,d).

        # Note:  If vectors (a,b)->(c,d) and (c,d)->(e,f) are exactly 180° opposed,
        #         or if either segment is zero-length, this function will do
        #         nothing; i.e. point (C,D) will not be set.

        c1 = c
        d1 = d
        c2 = c
        d2 = d
        # Calculate length of line segments
        dx1 = c - a
        dy1 = d - b
        dist1 = math.sqrt(dx1**2 + dy1**2)
        dx2 = e - c
        dy2 = f - d
        dist2 = math.sqrt(dx2**2 + dy2**2)
        # Exit if either segment is zero-length
        if math.isclose(dist1, 0.0,abs_tol=1e-09) or math.isclose(dist2, 0.0,abs_tol=1e-09):
            return 0,0,0
        # Inset each of the two line segments
        insetX = dy1/dist1*insetDist
        a += insetX
        c1 += insetX
        insetY = -dx1/dist1*insetDist
        b += insetY
        d1 += insetY
        insetX = dy2/dist2*insetDist
        e += insetX
        c2 += insetX
        insetY = -dx2/dist2*insetDist
        f += insetY
        d2 += insetY
        # If inset segments connect perfectly, return the connection point
        if math.isclose(c1, c2) and math.isclose(d1, d2,abs_tol=1e-09):
            return 1, c1, d1
        # Return the intersection point of the two inset segments (if any)
        #status, inX, inY = self.lineIntersection(a,b,c1,d1,c2,d2,e,f)
        status, inX, inY = self.lineIntersection(a,b,c1,d1,c2,d2,e,f)
        if status == 1:
            insetX = inX
            insetY = inY
            return 1, insetX, insetY

    def lineIntersection(self, Ax,Ay,Bx,By,Cx,Cy,Dx,Dy):
        # Converted from
        # public domain function by Darel Rex Finley, 2006

        # Determines the intersection point of the line defined by points A and B with the
        # line defined by points C and D.

        # Returns 1 if the intersection point was found, and returns that point in X,Y.
        # Returns 0 if there is no determinable intersection point, in which case X,Y will
        #be unmodified.

        # Fail if either line is undefined
        if (math.isclose(Ax, Bx) and math.isclose(Ay, By)) or (math.isclose(Cx, Dx) and math.isclose(Cy, Dy)):
            return 0, 0, 0
        # (1) Translate the system so that point A is on the origin
        Bx -= Ax
        By -= Ay
        Cx -= Ax
        Cy -= Ay
        Dx -= Ax
        Dy -= Ay
        # Discover the length of segment A-B
        distAB = math.sqrt(Bx**2 + By**2)
        # (2) Rotate the system so that point B is on the positive X axis
        theCos = Bx/distAB
        theSin = By/distAB
        newX = Cx*theCos + Cy*theSin
        Cy = Cy*theCos - Cx*theSin
        Cx = newX
        newX = Dx*theCos + Dy*theSin
        Dy = Dy*theCos - Dx*theSin
        Dx = newX
        # Fail if the lines are parallel
        if math.isclose(Cy, Dy):
            return 0,0,0
        # (3) Discover the position of the intersection point along line A-B
        ABpos = Dx + (Cx - Dx)*Dy/(Dy - Cy)
        # (4) Apply the discovered position to line A-B in the original coordinate system
        X = Ax + ABpos*theCos
        Y = Ay + ABpos*theSin
        return 1, X, Y

    ###############################

   

    def stringmeup(self,list1,scores,scores2,tscoremap,zerotab,cutout,cutoutpath,piece,layer,stylestring,tab_height,dashlength,tab_angle,mkpath):
        dscore = Path()
        plist1 = pathStruct()
        plist2 = pathStruct()
        plist3 = pathStruct()
        saveid = "a01"
        
                   
        
        for pt in range(len(list1)):
            if pt == 0:
                plist1.path.append(Move(list1[pt].x, list1[pt].y))
                plist2.path.append(Move(list1[pt].x, list1[pt].y))
            else:
                plist1.path.append(Line(list1[pt].x, list1[pt].y))
                
                plist2.path.append(Line(list1[pt].x, list1[pt].y))
        if (cutout != 0):  #here we handle second path which is inset and will be added to path
           
                    
            for pt in range(len(cutoutpath)):
                if pt == 0:
                    plist3.path.append(Move(cutoutpath[pt].x, cutoutpath[pt].y))
                else:
                    plist3.path.append(Line(cutoutpath[pt].x, cutoutpath[pt].y))

            ##### INSET THIS PIECE ####
            self.insetPolygon(plist3.path[0:-1],cutout)

            ###########
            
            #create new string from this
            istring = 'M ' + str(plist3.path[0].x) + ', '+str(plist3.path[0].y)
            for nd in reversed(range(1,len(plist3.path)-1)):
                istring += ' L '+ str(plist3.path[nd].x) +', '+ str(plist3.path[nd].y)
            #reverse istring?
            istring += ' Z'
            
            
        if len(scores) == 0:
            noscores = True
        else:
            noscores = False
        if len(tscoremap) == 0:
            notabs = True
        else:
            notabs = False
        
        newstring = 'M ' + str(round(list1[0].x ,4)) + ','+ str(round(list1[0].y,4))
                                                     
        for i in range(1,len(list1)-1):
            if i in tscoremap:
                
                tabpt2, tabpt1 = self.makeTab(plist2, list1[i], list1[i-1], tab_height, tab_angle)
                dscore = dscore + self.makescore(plist1.path[i],plist1.path[i-1],dashlength)
                newstring += ' L ' + str(round(tabpt1.x,4)) + ','+ str(round(tabpt1.y,4))
                newstring += ' L ' + str(round(tabpt2.x,4)) + ','+ str(round(tabpt2.y,4))
                               
            newstring += ' L ' + str(round(list1[i].x,4)) + ','+ str(round(list1[i].y,4))
        
        for i in range (len(scores)):
            dscore = dscore + self.makescore(plist1.path[scores[i]], plist1.path[scores2[i]],dashlength)
        
            
        if zerotab:
            zt= len(list1)-2
            tabpt2, tabpt1 = self.makeTab(plist2, list1[0], list1[zt], tab_height, tab_angle)
            dscore = dscore + self.makescore(plist1.path[0],plist1.path[zt],dashlength)
            newstring += ' L ' + str(round(tabpt1.x,4)) + ','+ str(round(tabpt1.y,4))
            newstring += ' L ' + str(round(tabpt2.x,4)) + ','+ str(round(tabpt2.y,4))
        newstring += ' Z '
        if cutout != 0:
            newstring1 = newstring + istring
            newstring = newstring1
        
        #NEED TO DRAW THIS
        dprop = Path(newstring)
        if math.isclose(dashlength, 0.0) or mkpath==False:
            # lump together all the score lines
            group = Group()
            group.label = 'group'+piece
            self.drawline(newstring,'model'+piece,group,stylestring) # Output the model
            if not (len(dscore)==0):
                stylestring2 =  {'stroke':'#009900','stroke-width':'0.25','fill':'#eeeeee'}
                self.drawline(str(dscore),'score'+piece,group,stylestring2) # Output the scorelines separately
            layer.append(group)
        else:
            dprop = dprop + dscore
            self.drawline(str(dprop),piece,layer,stylestring)
        #pc += 1
        return newstring

    #function to return the xy values for the top of the dormer.
    #when changing to inkscape we will need to call these with self.

    def geo_b_alpha_a(self,b, alpha):
        c= b/math.cos(math.radians(alpha))
        a = math.sqrt(c**2-b**2)
        return a
    
    def geo_b_alpha_c(self,b, alpha):
        c=b/math.cos(math.radians(alpha))
        return c

    def geo_a_b_alpha(self,a,b):
        c=math.sqrt(a**2+b**2)
        alpha = math.asin(a/c)
        return math.degrees(alpha)

    def geo_a_b_c(self,a,b):
        c=math.sqrt(a**2+b**2)
        return c

    def geo_c_a_b(self,c,a):
        b= math.sqrt(c**2 - a**2)
        return b
        
    def geo_a_alpha_b(self,a, alpha):
        c=a/math.sin(math.radians(alpha))
        b= math.sqrt(c**2 - a**2)
        return b

    def nodelocs(self,size,baseht, sides,peakdown):  #dormer top polygon 
        xlist = []
        ylist = []
        
        angel = 360/sides
        k = (math.floor(1+sides/4))
        
        for i in range(k):
            xlist.append(round(math.cos(math.radians(angel*i))*size,6))
            ylist.append(round(math.sin(math.radians(angel*i))*size,6))
            #return the base and polygon node x and y vals for half the top
            #the x val will be negative for the left side when drawing the hole or front
        peaky = (ylist[k-1])- (ylist[k-2])
        if k>1:
            peakdelta = ylist[k-1]-ylist[k-2] #the peak can be reduced a percentage of this
            #reduce the height of the node by peakdelta*peakdown
            pd = peakdelta*peakdown
            ylist[k-1] = (ylist[k-1]) - pd
            peaky = ylist[k-1]
        

        return xlist,ylist,peaky

    def outsets (self,ylist, roofangle,baseht,isabase,sides):  #how far will our dormer nodes be from the roof?
        outsetlen = []
        #first will be at the height of the base if there is one
        if isabase:
            totht = baseht
            
        else:
            totht = 0

        if sides == 0:
            outsetlen.append(self.geo_b_alpha_a(baseht,90-roofangle))
                             
        for i in range(len(ylist)): 
            y2 = totht + ylist[i]
            #calculate the hypotenuse given alpha=roofangle and a=totht
            outsetlen.append( self.geo_b_alpha_a(y2,90-roofangle))
            
        return outsetlen  #contains the outset for the polygon top 


    def holenodes(self,xlist,ylist, baseht, basewd,roofangle,isabase,sides):  #plot the hole part
        hpathlist = []
          
        halfbase = .5*basewd
        if isabase:
            #start bottom left of base
            baselong = self.geo_b_alpha_c(baseht,90-roofangle)
            hpath = RNodes(-halfbase,baselong)
            hpathlist.append(hpath)
            hpath = RNodes(halfbase,baselong)
            hpathlist.append(hpath)
        if sides>0:
            for i in range(len(xlist)-1):
                #calculate stretched y
                newy = self.geo_b_alpha_c(ylist[i],90-roofangle)
                hpath = RNodes(xlist[i],-newy)
                hpathlist.append(hpath)

            for i in reversed(range(len(xlist))):
                #calculate stretched
                newy = self.geo_b_alpha_c(ylist[i],90-roofangle)
                hpath = RNodes(-xlist[i],-newy)
                hpathlist.append(hpath)
        else:
            hpath = RNodes(halfbase,0)
            hpathlist.append(hpath)
            hpath= RNodes(-halfbase,0)
            hpathlist.append(hpath)
      
        #go back to origin  
        hpath = RNodes(hpathlist[0].x,hpathlist[0].y)
        hpathlist.append(hpath)

        return hpathlist

    def sidenodes(self,outset,sideln,baseht,basewd,isabase,stickout,dmult,sides):
        #add code to return a tscoremap and scoremap
        spathlist = []
        
        sidelna = sideln *dmult      
        xzero = round(stickout,4) #if base sticks out we subtract this from the x zero loc
        smap = []
        smapr = []
        tmap = []
        sny = 0
        s = 0
        t = 0
        
        #first the base
        if sides == 0:
            spath = RNodes(-xzero,0) #0
            spathlist.append(spath)
            
        if isabase:
            spath = RNodes(-xzero,baseht)
            spathlist.append(spath) #1
            tmap.append(t)
            s += 1
            t += 1
            if(xzero > 0):
                spath = RNodes(0,baseht)
                spathlist.append(spath)
                s += 1
                t += 1
       
        if sides == 0:
            spath = RNodes(outset[0],0)
            spathlist.append(spath) #2
            
                
        #NOW THE DORMER TOP - omit if sides is 0        
        if sides >0:     
            for i in range(len(outset)-1):
                # x is outset[i] and y is  i*sidelength
                spath = RNodes(outset[i],-i*sidelna)
                spathlist.append(spath)
                sidesdone = i+1
                smap.append(s)
                tmap.append(t)
                s += 1
                t += 1
                
            
            for i in reversed(range(len(outset))):
                sny = -(sidesdone)*sidelna
                spath = RNodes(outset[i],sny)
                spathlist.append(spath)
                sidesdone +=1
                smap.append(s)
                tmap.append(t)
                s += 1
                t += 1
        else:
            #add in the width of the dormer also need tabs in place
            sny = -basewd
            spath = RNodes(outset[0],sny)
            spathlist.append(spath) #2

        if isabase:
            sny = sny-baseht
            spath = RNodes(0,sny)
            spathlist.append(spath) #3
            tmap.append(t)
            s += 1
            t += 1
            
            
        if xzero > 0:
            spath = RNodes(-xzero,sny)
            spathlist.append(spath)
            s+=1

        if isabase:
            sny = sny + baseht
       
        for i in range(int(sides/2)+1): 
            spath = RNodes(-xzero,sny)
            spathlist.append(spath)
            smapr.append(s)
            s +=1
            sny = sny +sidelna

        if sides == 0:
            if(xzero > 0):
                smap =[3,4]
                smapr =[7,0]
                tmap = [2,3,4,5,6]  
                
            else:
                smap = [2,3]
                smapr = [5,0]
                tmap = [2,3,4]  
             
      

            
        #go back to origin if needed

        spath = RNodes(spathlist[0].x,spathlist[0].y)
        spathlist.append(spath)
        
        #smap now has all the node nums for start node of scorelines  
        #smapr has the corresponding end node nums for scorelines
        # e.g. if smap=[1] and smapr=[2] there would be a scoreline between the second and third nodes (zero index)
        #tmap has the nodes (n) to make tabs with (n-1)

        smapr.reverse()
        return spathlist,smap,smapr,tmap

    def frontnodes(self,xlist,ylist,baseht,basewidth,isabase,stickout,sides):
        
        fpathlist = []
        fshortlist = []
        tmap = []
        smap = []
        smapr = []
        t=0
        stuckout =False
        hw=basewidth*.5
        if isabase:
            fpath = RNodes(-hw,baseht)
            fshortpath = RNodes(-hw,baseht)
            fpathlist.append(fpath)
            fshortlist.append(fshortpath)
            t += 1
            if stickout > 0:                
                fpath = RNodes(-hw,baseht+stickout)
                fpathlist.append(fpath)
                tmap.append(t)
                t += 1
                fpath = RNodes(hw,baseht+stickout)
                fpathlist.append(fpath)
                tmap.append(t)
                t += 1
                smap = [0]
                smapr =[3]
                
            fpath = RNodes(hw,baseht)
            fshortpath = RNodes(hw,baseht)
            fpathlist.append(fpath)
            fshortlist.append(fshortpath)
            tmap.append(t)
            t += 1
        else:
            if stickout > 0:                
                fpath = RNodes(-hw,stickout)
                fpathlist.append(fpath)
                tmap.append(t)
                t += 1
                fpath = RNodes(hw,stickout)
                fpathlist.append(fpath)
                tmap.append(t)
                t += 1
                stuckout = True
                

        #IF there is a polygon top
        if sides>0:
            for i in range (len(xlist)):
                hw=  xlist[i]
                fpath = RNodes(hw,-ylist[i])
                fpathlist.append(fpath)
                fshortpath = RNodes(hw,-ylist[i])
                fshortlist.append(fshortpath)
                tmap.append(t)
                t += 1
            ct=0
            
            for i in reversed((range(len(xlist)-1))):
                hw = xlist[i]
                ct +=2
                y= fpathlist[len(fpathlist)-ct].y
                fpath = RNodes(-hw,y)
                fpathlist.append(fpath)
                
                y= fshortlist[len(fshortlist)-ct].y
                fshortpath = RNodes(-hw,y)
                fshortlist.append(fshortpath)
                tmap.append(t)
                t += 1
        else:
            fpath =RNodes(hw,0)
            fpathlist.append(fpath)
            fshortpath = RNodes(hw,0)
            fshortlist.append(fshortpath)
            fpath = RNodes(-hw,0)
            fpathlist.append(fpath)
            fshortpath = RNodes(-hw,0)
            fshortlist.append(fshortpath)
        if stuckout and (isabase == False):
            smap=[2]
            smapr=[t-1]
        #back to origin
        fpath = RNodes(fpathlist[0].x,fpathlist[0].y)
        fpathlist.append(fpath)
        fshortpath = RNodes(fshortlist[0].x,fshortlist[0].y)
        fshortlist.append(fshortpath)
        
        tmap.append(t)
        return fpathlist,fshortlist,smap,smapr,tmap

    def roofsidenodes(self,halfdepth,side_inset_ht,bbx,bty,roofpeak,isbarn):
        rsidepathlist = []
        #btx = bdratio*halfdepth  
        #bty = roofpeak*bhratio  
        #bbx = halfdepth - btx           
        #bby = roofpeak-bty   
        #fixed 12-31-2021
        if  not isbarn: # not a barn
            rsidepath = RNodes(0,0)
            rsidepathlist.append(rsidepath) #0
            rsidepath = RNodes(halfdepth,side_inset_ht)
            rsidepathlist.append(rsidepath) #1
            rsidepath = RNodes(-halfdepth,side_inset_ht)
            rsidepathlist.append(rsidepath) #2
            rsidepath = RNodes(0,0)
            rsidepathlist.append(rsidepath) #3
            tmap = [1,2]
            smap =[]
            smapr = []
            
        else: #is a barn
            rsidepath = RNodes(0,0)
            rsidepathlist.append(rsidepath) #0
            
            rsidepath = RNodes(bbx,bty)
            rsidepathlist.append(rsidepath) #1
            
            rsidepath = RNodes(halfdepth,roofpeak)
            rsidepathlist.append(rsidepath) #2
            
            rsidepath = RNodes(-halfdepth,roofpeak)
            rsidepathlist.append(rsidepath) #3
            
            rsidepath = RNodes(-bbx,bty)
            rsidepathlist.append(rsidepath) #4 
            
            rsidepath = RNodes(0,0) #back to origin
            rsidepathlist.append(rsidepath) #5
            
            tmap = [1,2,3,4,5]
            smap =[1]
            smapr = [5]
        return rsidepathlist,smap,smapr,tmap

    def roofmainnodes(self,roof_inset,roof_top_width,roofwidth,roof_actual_ht,bbx,bby,btx,bty,bb_ln,bt_ln,isbarn):
        smap=[]
        smapr=[]
        tmap = []
        rpathlist=[]
        if not(isbarn):
            rpath = RNodes(roof_inset,0) #0
            rpathlist.append(rpath)
            
            rpath = RNodes(roof_inset+roof_top_width,0)
            rpathlist.append(rpath) #1
            
            rpath = RNodes(roofwidth,roof_actual_ht)
            rpathlist.append(rpath) #2
            
            rpath = RNodes(0,roof_actual_ht)
            rpathlist.append(rpath) #3
            
            rpath = RNodes(roof_inset,0)
            rpathlist.append(rpath) #4
            tmap.append(1)
            tmap.append(3)
                    
        else:
            
            rpathlist =[]
            bbtoty = bb_ln+bt_ln
            rpath = RNodes(0,0)
            rpathlist.append(rpath) #0
            rpath = RNodes(roofwidth,0)
            rpathlist.append(rpath) #1
            rpath = RNodes(roofwidth,bt_ln)
            rpathlist.append(rpath) #2
            rpath = RNodes(roofwidth,bbtoty)
            rpathlist.append(rpath) #3
            rpath = RNodes(0,bbtoty)
            rpathlist.append(rpath) #4
            rpath = RNodes(0,bt_ln)
            rpathlist.append(rpath) #5
            rpath = RNodes(0,0)
            rpathlist.append(rpath) #6
            smap.append(2)   #one end of score mark
            smapr.append(5)  #other end of score mark
            tmap.append(1)
            tmap.append(4)       
        return rpathlist,smap,smapr, tmap
        
    def makeChimney(self,rp,rd,ch,cw,cd,oc):
        chholelist = []
        mypath = pathStruct()
        tmap = [1,2,3,4,5]
        smap =[1]
        smapr = [5]
        chpathlist =[]
        fslant = 0
        bslant = 0
        ra = self.geo_a_b_alpha(rp,rd)	#roof angle
        ca = 90-ra                      #outside angle

        fsd = oc*cd #proportion toward front.
        
        bsd = cd-fsd  #the rest 
        
        bsh = self.geo_a_alpha_b(bsd, ca) #back side height
        
        fsh = self.geo_a_alpha_b(fsd,ca)  #front side height 
        

        chhole = RNodes(0,0)
        chholelist.append(chhole)
        if fsd> 0:
            fslant = self.geo_a_b_c(fsd,fsh)
        if bsd >0:
           bslant = self.geo_a_b_c(bsd,bsh)
           chhole = RNodes(bslant,0)
           chholelist.append(chhole)
        chhole = RNodes(bslant+fslant, 0)
        chholelist.append(chhole)
        chhole = RNodes(bslant+fslant,cw)
        chholelist.append(chhole)
        if bsd > 0:
            chhole = RNodes(bslant,cw)
            chholelist.append(chhole)
        chhole = RNodes(0,cw)
        chholelist.append(chhole)
        chhole = RNodes(0,0)
        chholelist.append(chhole)
        if (bsd > 0) and (fsd >0):
            chholescore = [1]
            chholescore2 = [4]
        
            
                   
        #inkex.utils.debug("ch={}  bsh={}  fsh={}".format(ch,bsh,fsh))
        cpathx = [0, bsd, cd, cd+cw,  cw+(2*cd)-bsd, (2*cd)+cw, 2*(cd+cw)]
        cpathy = [ch+bsh,ch,ch+fsh,ch+fsh,ch,ch+bsh,ch+bsh]
        
        mypath.path.append(Move(0,0))
        rpath = RNodes(0,0)
        chpathlist.append(rpath)
        
        plen = len(cpathx)
        for i in range(1,plen):
            if cpathx[i]  != mypath.path[-1].x:
                mypath.path.append(Line(cpathx[i],0))
                rpath = RNodes(cpathx[i],0)
                chpathlist.append(rpath)
                
        for i in reversed(range(plen)):
            yp = cpathy[i]
            if not ((cpathx[i] == mypath.path[-1].x) and  (yp == mypath.path[-1].y)):
                mypath.path.append(Line(cpathx[i],yp))
                rpath = RNodes(cpathx[i],yp)
                chpathlist.append(rpath)
        #inkex.utils.debug("mypath.path[-2]xy is {},{}".format(mypath.path[-1].x,mypath.path[-1].y))
        #inkex.utils.debug("chpathlist[-1]xy is {},{}".format(chpathlist[-1].x,chpathlist[-1].y))
        mypath.path.append(ZoneClose())
        rpath = RNodes(0,0)
        chpathlist.append(rpath)
        #scorelines between 2,3 and 5 if off_center, but only between 1,2,3inkex.utils.debug("len chpathlist is {}".format(len(chpathlist)))
        if len(chpathlist) == 11:  #this is not off-center
            smap = [1,2,3]
            smapr = [8,7,6]
            tmap = [5,6,7,8,9]
        else:
            tmap= [7,8,9,10,11,12,13]
            smap = [2,3,5]
            smapr = [11,10,8]
            
            
        #and the hole template:
        
        return(chpathlist,smap,smapr,tmap,chholelist,chholescore,chholescore2)
        
        
        
        
        
    def roofbasenodes(self,roofwidth,roofdepth):
        smap=[]
        smapr=[]
        tmap = []
        rbaselist=[]
        rpath = RNodes(0,0) #0
        rbaselist.append(rpath)
        
        rpath = RNodes(roofwidth,0)
        rbaselist.append(rpath) #1
        
        rpath = RNodes(roofwidth,roofdepth)
        rbaselist.append(rpath) #2
        
        rpath = RNodes(0,roofdepth)
        rbaselist.append(rpath) #3
        
        rpath = RNodes(0,0)
        rbaselist.append(rpath) #4
        return rbaselist



        
    def effect(self):
        ###############################################      
        ###START ROOF MAKER PROPER
        scale = self.svg.unittouu('1'+self.options.unit)
        layer = self.svg.get_current_layer()
        #Get the input options 
        if self.options.isbarn == "True":
            isbarn = True
        else:
            isbarn = False
        if self.options.isabase == "True":
            isabase = True
        else:
            isabase = False
        dormerht = float(self.options.dormerht)*scale
        basewidth  = float(self.options.basewidth)*scale
        roofpeak  = float(self.options.roofpeak)*scale
        roofdepth = float(self.options.roofdepth)*scale
        roofwidth = float(self.options.roofwidth)*scale
        roof_inset  = float(self.options.roof_inset)*scale
        bhratio = float(self.options.bhratio)
        bdratio = float(self.options.bdratio)
        sides = int(self.options.sides)
        stickout = float(self.options.stickout)*scale
        window_frame = float(self.options.window_frame)
        peakdown= float(self.options.peak_down)
        scoretype = self.options.scoretype
        chimney_ht = float(self.options.chimney_ht)*scale
        chimney_wd = float(self.options.chimney_wd)*scale
        chimney_depth =float(self.options.chimney_depth)*scale
        off_center = float(self.options.off_center)
        shrink = float(self.options.shrink)
        #Set some defaults
        mincutout = 1*scale
        tabht = 0.25*scale
        if scoretype == "dash":
            dashln = 0.1*scale
        else:
            dashln = 0
        tabangle = 45
        struct_style   = {'stroke':'#000000','stroke-width':'0.25','fill':'#ffd5d5'}
        deco_style = {'stroke':'#000000','stroke-width':'0.25','fill':'#80e5ff'}
        hole_style = {'stroke':'#000000','stroke-width':'0.25','fill':'#aaaaaa'}

        #initialize some variables
        btx = bty = bbx = bby = bt_ln = 0
        
        xlist =[]
        ylist = []
        outsetslist = []
        rpathlist = []
        chpathlist =[]
        cutout = 0 
        dmult = 1.04
        sidescores = []
        sidescores2 = []
        sidetabs = []
        side_deco_scores =[]
        side_deco_scores2 = []
        emptyset = []
        if math.isclose(dormerht,0,abs_tol=1e-09):
            dodormers = False
            baseht = dormerht
        else:
            dodormers = True
            if (sides > 0):
                baseht = dormerht - .5*basewidth
            else:
                baseht = dormerht
            dhalfwidth = .5*basewidth
           
         
        ##initial calculations

        if math.isclose(roof_inset,0,abs_tol=1e-09):
            no_inset = True
        else:
            no_inset = False

        halfdepth = roofdepth/2
        base_angle = self.geo_a_b_alpha(roofpeak, halfdepth)
        roof_actual_ht = self.geo_a_b_c(roofpeak, roofdepth/2)
        roof_inset_ht = self.geo_a_b_c(roof_actual_ht,roof_inset)
        roof_top_width = roofwidth-(2*roof_inset)
               
        if no_inset:
            side_inset_ht = roofpeak
        else :
            side_inset_ht = self.geo_c_a_b(roof_inset_ht, halfdepth)
            
        if dodormers:
            sidelen = 0
            peaky=0
            if (sides >0):
                sidelen = basewidth * math.sin(math.pi/sides)  #length of polygon side
                #isabase = not(math.isclose(baseht,0.0, abs_tol = 1e-09))
                xlist, ylist,peaky = self.nodelocs(basewidth/2,baseht, sides,peakdown) #hts of polygon points
            


        btx = bdratio*halfdepth  
        bty = roofpeak*bhratio  
        
        bbx = halfdepth - btx           
        bby = roofpeak-bty   
        if (isbarn):
            barn_base_angle = self.geo_a_b_alpha(bby, bbx)
        bt_ln = self.geo_a_b_c(bbx,bty) 
        #fixed 12-31-2021
        bb_ln = self.geo_a_b_c( btx,bby) 
        #fixed 12-31-2021
        bbtoty = bt_ln + bb_ln          
        
        outsetslist = self.outsets(ylist,base_angle,baseht,isabase,sides) #outsets are used in dormer side pieces
        zerotab = False
        #start construction

        mkpath = True
        if ((not isabase) and (sides == 0)) or not dodormers: #sanity check - don't do dormers without tops or bottoms or if we already turned them off
            dodormers = False
        else:
            dodormers = True
    
           
        
        #ROOF BASE
        ctout = min(mincutout,.35*roofdepth)
        cutout = -ctout
        zerotab = False
        roofbaselist = self.roofbasenodes(roofwidth,roofdepth)
        svgroofbase = self.stringmeup(roofbaselist,emptyset,emptyset,emptyset, zerotab,cutout,roofbaselist,"Roof_Base",layer,struct_style,tabht,dashln,tabangle,mkpath)
                                    
        
        #ROOF SIDE AND ROOF SIDE DECO
        cutout = 0
        roofsidelist,roofsidescore,roofsidescore2,roofsidetabs = self.roofsidenodes(halfdepth,side_inset_ht,bbx,bty,roofpeak,isbarn)
        #fixed 12-31-2021
        zerotab = True
        svgroofside = self.stringmeup(roofsidelist,roofsidescore,roofsidescore2,roofsidetabs,zerotab,cutout,roofsidelist,"Side_of_Roof",layer,struct_style,tabht,dashln,tabangle,mkpath)
        svgroofside = self.stringmeup(roofsidelist,roofsidescore,roofsidescore2,roofsidetabs,zerotab,cutout,roofsidelist,"Side_of_Roof2",layer,struct_style,tabht,dashln,tabangle,mkpath)
        zerotab = False
        svgroofside_deco = self.stringmeup(roofsidelist,roofsidescore, roofsidescore2,emptyset,zerotab,0,roofsidelist,"Side_of_RoofDeco",layer,deco_style,tabht,dashln,tabangle,mkpath)
        svgroofside_deco = self.stringmeup(roofsidelist,roofsidescore, roofsidescore2,emptyset,zerotab,0,roofsidelist,"Side_of_RoofDeco2",layer,deco_style,tabht,dashln,tabangle,mkpath)
         
        #ROOF MAIN, ROOF MAIN 2 AND ROOF MAIN DECO
        roofmainlist,roofmainscore,roofmainscore2,roofmaintabs = self.roofmainnodes(roof_inset,roof_top_width,roofwidth,roof_actual_ht,bbx,bby,btx,bty,bb_ln,bt_ln,isbarn)
        zerotab = False
        svgroofmain = self.stringmeup(roofmainlist,roofmainscore, roofmainscore2,roofmaintabs,zerotab,cutout,roofmainlist,"Main_Roof",layer,struct_style,tabht,dashln,tabangle,not mkpath)
        #remove the top tab on this one,but leave the bottom
        roofmaintabs.pop(0)
        svgroofmain2 = self.stringmeup(roofmainlist,roofmainscore, roofmainscore2,roofmaintabs,zerotab,cutout,roofmainlist,"Main_Roof_2",layer,struct_style,tabht,dashln,tabangle,not mkpath)
        zerotab = False
        svgroofmain_deco = self.stringmeup(roofmainlist,roofmainscore, roofmainscore2,emptyset,zerotab,0,roofmainlist,"Main_Roof_Deco",layer,deco_style,tabht,dashln,tabangle,not mkpath)
        svgroofmain_deco = self.stringmeup(roofmainlist,roofmainscore, roofmainscore2,emptyset,zerotab,0,roofmainlist,"Main_Roof_Deco2",layer,deco_style,tabht,dashln,tabangle,not mkpath)
        if dodormers:
             #FRONT PANE, FRONT AND FRONT DECO
            window_inset = window_frame*basewidth
            if (window_inset> dhalfwidth) or  (window_inset>.5 * peaky):
                window_inset = window_frame * min(dhalfwidth*.75, peaky) 
            if peaky == 0:
                window_inset = window_frame*basewidth
            cutout = window_inset
            
            frontlist,frontshortlist,frontscore,frontscore2,fronttabs = self.frontnodes(xlist,ylist,baseht,basewidth,isabase,stickout,sides) #front of dormer        
            zerotab = True  #add a tab between start and end nodes
            #do deco
            svgfront = self.stringmeup(frontlist,frontscore,frontscore2,fronttabs,zerotab,cutout,frontshortlist,"Front_Path",layer,struct_style,tabht,dashln/2,tabangle,mkpath)
            svgfront_deco = self.stringmeup(frontshortlist,emptyset,emptyset,emptyset,not zerotab,cutout,frontshortlist,"Front_Deco_Path",layer,deco_style,tabht,dashln,tabangle,mkpath)
            
            

            #HOLE 12-30
            if (isbarn):
                base_angle = barn_base_angle
            holepathlist = self.holenodes(xlist,ylist,baseht,basewidth,base_angle,isabase,sides) #hole path
            self.stringmeup(holepathlist,emptyset,emptyset,emptyset,0,0,holepathlist,"Hole",layer,hole_style,tabht,dashln,tabangle,mkpath)
            
            #DORMER SIDE
            sidepathlist,sidescores,sidescores2,sidetabs = self.sidenodes(outsetslist,sidelen,baseht,basewidth,isabase,stickout,dmult,sides) #side of dormer
            zerotab = False
            cutout = 0
            svgside = self.stringmeup(sidepathlist,sidescores,sidescores2,sidetabs,zerotab,cutout,sidepathlist,"Dormer_Side",layer,struct_style,tabht,dashln/2,tabangle/2,mkpath)
            #grab the middle score line for the deorative strip, but don't put on any tabs
            if sides>0:
                d=math.floor((len(sidescores)-1)/2)
                side_deco_scores.append(sidescores[d])
                side_deco_scores2.append(sidescores2[d])
            else:
                side_deco_scores =sidescores
                side_deco_scores2 = sidescores2
                zerotab = False
            svgside_deco = self.stringmeup(sidepathlist,side_deco_scores,side_deco_scores2,emptyset,zerotab,cutout,sidepathlist,"Dormer_Side_Deco",layer,deco_style,tabht,dashln,tabangle,mkpath)
            
        #CHIMNEY
        
        if not( (chimney_wd==0) or (chimney_depth==0)):
            chimneylist,chscores, chscores2,chtabs,chholelist,chholescore,chholescore2=self.makeChimney(roofpeak,roofdepth,chimney_ht,chimney_wd,chimney_depth,off_center)
            zerotab = False
            cutout = 0
            chimneypiece = self.stringmeup(chimneylist,chscores,chscores2, chtabs,zerotab,cutout,chimneylist,"Chimney",layer,struct_style,tabht*shrink,dashln*shrink,tabangle*shrink,mkpath)
            chimneypiece2 = self.stringmeup(chimneylist,chscores,chscores2, emptyset,zerotab,cutout,chimneylist,"Chimneydeco",layer,deco_style,tabht,dashln,tabangle,mkpath)
            chimneyhole = self.stringmeup(chholelist,chholescore,chholescore2, emptyset,zerotab,cutout,chholelist,"Chimneyhole",layer,hole_style,tabht,dashln,tabangle,mkpath)
            
if __name__ == '__main__':
    Roofmaker().run()
