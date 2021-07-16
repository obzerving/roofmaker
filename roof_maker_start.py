import inkex
import math
import copy

#Need to fix dormer extension
class pathStruct(object):
    def __init__(self):
        self.id="path0000"
        self.path=[]
        self.enclosed=False
    def __str__(self):
        return self.path
    
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
        pars.add_argument("--barn_type",default="0",\
            help="User barn style top on roof (two angles)")
        pars.add_argument("--dormer_poly_sides", default="12",\
            help="Dormer Top Poly Sides")
        pars.add_argument("--window_inset_size", type=float, default=1.0,\
            help="Window Inset (in Dimensional Units)")
        pars.add_argument("--dormer_width", type=float, default=1.0,\
            help="Dormer Width (in Dimensional Units)")
        pars.add_argument("--dormer_height", type=float, default=1.5,\
            help="Dormer Height (in Dimensional Units; zero for no dormer)")
        pars.add_argument("--roof_inset", type=float, default=1.0,\
            help="Roof Inset (in Dimensional Units)")
        pars.add_argument("--roof_peak_ht", type=float, default=2.0,\
            help="Roof Peak Height (in Dimensional Units)")
        pars.add_argument("--roof_base_depth", type=float, default=3.0,\
            help="Roof Base Depth (in Dimensional Units)")
        pars.add_argument("--roof_base_width", type=float, default=7.0,\
            help="Roof Base Width (in Dimensional Units)")

        pars.add_argument("--no_base",type=int,default=0,\
            help="Omit base rectangle on dormer")
        pars.add_argument("--peak_down",type=float,default=1.0,\
            help="Extend Base of dormer")
        pars.add_argument("--extend_base",type=float,default=0.0,\
            help="Extend base of dormer from flush with roof")
        pars.add_argument("--window_frame",type=float,default=0.125,\
            help="Relative thickness of dormer window frame")
            
        pars.add_argument("--barn_ratio",type=float,default=0.2,\
            help="Relative thickness of dormer window frame")
        pars.add_argument("--barn_depth_ratio",type=float,default=0.4,\
            help="Relative thickness of dormer window frame")
        

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
        
    #define a bunch of geometric formulas  for right triangles
    def geo_a_c_alpha(self,a,c):
        alpha = math.asin(a / c)
        return math.degrees(alpha)
        
    def geo_b_c_alpha(self,b,c):
        a= math.sqrt(c**2 - b**2)
        alpha = math.asin(a/c)
        return math.degrees(alpha)
        
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
        
    def geo_b_alpha_c(self,b, alpha):
        c=b/math.cos(math.radians(alpha))
        return c
        
    def geo_a_alpha_b(self,a, alpha):
        c=a/math.sin(math.radians(alpha))
        b= math.sqrt(c**2 - a**2)
        return b
        
    def geo_a_alpha_c(self,a,alpha):
        c=a/math.sin(math.radians(alpha))
        return c

    def geo_c_b_a (self,c,b):
        a=math.sqrt(c**2-b**2)
        return a
        
    def geo_a_b_beta(self,a,b):
        c=math.sqrt(a**2 + b**2)
        beta=math.asin(b/c)
        return math.degrees(beta)
        
    def geo_a_c_beta(self,a,c):
        b=math.sqrt(c**2 - a**2)
        beta = asin(b/c)
        return math.degrees(beta)
        
    def geo_b_c_beta(self,b,c):
        math.asin(b/c)
        return math.degrees(beta)
        
    def geo_c_alpha_b(self,c,alpha):
        a = c * math.sin(math.radians(alpha))
        b = math.sqrt(c**2 - a**2)
        return(b)
        
    def geo_c_alpha_a(self,c,alpha):
        a= c * math.sin(math.radians(alpha))
        return(a)
    
    def geo_a_beta_c(self,a, beta):
        c = a/math.cos(math.radians(a))
        return (c)
        
    def geo_b_beta_c(self,b, beta):
        c = b/math.sin(math.radians(beta))
        return (c)


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
            status, px, py = self.insetCorner(a,b,c,d,e,f,insetDist)
            if status == 1:
                points[i].x = px
                points[i].y = py
            
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

    def makescore(self, pt1, pt2, dashlength):
        # Draws a dashed line of dashlength between two points
        # Dash = dashlength (in inches) space followed by dashlength mark
        # if dashlength is zero, we want a solid line
        apt1 = inkex.paths.Line(0.0,0.0)
        apt2 = inkex.paths.Line(0.0,0.0)
        ddash = ''
        if math.isclose(dashlength, 0.0):
            #inkex.utils.debug("Draw solid dashline")
            ddash = ' M '+str(pt1.x)+','+str(pt1.y)+' L '+str(pt2.x)+','+str(pt2.y)
        else:
            if math.isclose(pt1.y, pt2.y):
                #inkex.utils.debug("Draw horizontal dashline")
                if pt1.x < pt2.x:
                    xcushion = pt2.x - dashlength
                    xpt = pt1.x
                    ypt = pt1.y
                else:
                    xcushion = pt1.x - dashlength
                    xpt = pt2.x
                    ypt = pt2.y
                ddash = ''
                done = False
                while not(done):
                    if (xpt + dashlength*2) <= xcushion:
                        xpt = xpt + dashlength
                        ddash = ddash + ' M ' + str(xpt) + ',' + str(ypt)
                        xpt = xpt + dashlength
                        ddash = ddash + ' L ' + str(xpt) + ',' + str(ypt)
                    else:
                        done = True
            elif math.isclose(pt1.x, pt2.x):
                #inkex.utils.debug("Draw vertical dashline")
                if pt1.y < pt2.y:
                    ycushion = pt2.y - dashlength
                    xpt = pt1.x
                    ypt = pt1.y
                else:
                    ycushion = pt1.y - dashlength
                    xpt = pt2.x
                    ypt = pt2.y
                ddash = ''
                done = False
                while not(done):
                    if(ypt + dashlength*2) <= ycushion:
                        ypt = ypt + dashlength         
                        ddash = ddash + ' M ' + str(xpt) + ',' + str(ypt)
                        ypt = ypt + dashlength
                        ddash = ddash + ' L ' + str(xpt) + ',' + str(ypt)
                    else:
                        done = True
            else:
                #inkex.utils.debug("Draw sloping dashline")
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
                ddash = ''
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
                        ddash = ddash + ' M ' + str(xpt) + ',' + str(ypt)
                        # draw the mark
                        xpt = xpt - msign*dashlength*math.cos(theta)
                        ypt = ypt - msign*dashlength*math.sin(theta)
                        ddash = ddash + ' L ' + str(xpt) + ',' + str(ypt)
                    else:
                        done = True
        return ddash

    def insidePath(self, path, p):
        point = pnPoint((p.x, p.y))
        pverts = []
        for pnum in path:
            pverts.append((pnum.x, pnum.y))
        isInside = point.InPolygon(pverts, True)
        return isInside # True if point p is inside path

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

    def makeTab(self, tpath, pt1, pt2, tabht, taba):
        # tpath - the pathstructure containing pt1 and pt2
        # pt1, pt2 - the two points where the tab will be inserted
        # tabht - the height of the tab
        # taba - the angle of the tab sides
        # returns the two tab points in order of closest to pt1
        tpt1 = inkex.paths.Line(0.0,0.0)
        tpt2 = inkex.paths.Line(0.0,0.0)
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
                    tpt1.x = pt1.x + testHt
                    tpt2.x = pt2.x + testHt
                    tpt1.y = pt1.y + testHt/math.tan(math.radians(testAngle))
                    tpt2.y = pt2.y - testHt/math.tan(math.radians(testAngle))
                    pnpt1 = inkex.paths.Move(tpt1.x, tpt1.y)
                    pnpt2 = inkex.paths.Move(tpt2.x, tpt2.y)
                    if ((not tpath.enclosed) and (self.insidePath(tpath.path, pnpt1) or self.insidePath(tpath.path, pnpt2))) or \
                       (tpath.enclosed and ((not self.insidePath(tpath.path, pnpt1)) and (not self.insidePath(tpath.path, pnpt2)))):
                        tpt1.x = pt1.x - currTabHt
                        tpt2.x = pt2.x - currTabHt
                    else:
                        tpt1.x = pt1.x + currTabHt
                        tpt2.x = pt2.x + currTabHt
                    tpt1.y = pt1.y + currTabHt/math.tan(math.radians(currTabAngle))
                    tpt2.y = pt2.y - currTabHt/math.tan(math.radians(currTabAngle))
                else: # pt2.y < pt1.y
                    tpt1.x = pt1.x + testHt
                    tpt2.x = pt2.x + testHt
                    tpt1.y = pt1.y - testHt/math.tan(math.radians(testAngle))
                    tpt2.y = pt2.y + testHt/math.tan(math.radians(testAngle))
                    pnpt1 = inkex.paths.Move(tpt1.x, tpt1.y)
                    pnpt2 = inkex.paths.Move(tpt2.x, tpt2.y)
                    if ((not tpath.enclosed) and (self.insidePath(tpath.path, pnpt1) or self.insidePath(tpath.path, pnpt2))) or \
                       (tpath.enclosed and ((not self.insidePath(tpath.path, pnpt1)) and (not self.insidePath(tpath.path, pnpt2)))):
                        tpt1.x = pt1.x - currTabHt
                        tpt2.x = pt2.x - currTabHt
                    else:
                        tpt1.x = pt1.x + currTabHt
                        tpt2.x = pt2.x + currTabHt
                    tpt1.y = pt1.y - currTabHt/math.tan(math.radians(currTabAngle))
                    tpt2.y = pt2.y + currTabHt/math.tan(math.radians(currTabAngle))
            elif math.isclose(pt1.y, pt2.y):
                # It's horizontal. Let's try the top
                if pt1.x < pt2.x:
                    tpt1.y = pt1.y - testHt
                    tpt2.y = pt2.y - testHt
                    tpt1.x = pt1.x + testHt/math.tan(math.radians(testAngle))
                    tpt2.x = pt2.x - testHt/math.tan(math.radians(testAngle))
                    pnpt1 = inkex.paths.Move(tpt1.x, tpt1.y)
                    pnpt2 = inkex.paths.Move(tpt2.x, tpt2.y)
                    if ((not tpath.enclosed) and (self.insidePath(tpath.path, pnpt1) or self.insidePath(tpath.path, pnpt2))) or \
                       (tpath.enclosed and ((not self.insidePath(tpath.path, pnpt1)) and (not self.insidePath(tpath.path, pnpt2)))):
                        tpt1.y = pt1.y + currTabHt
                        tpt2.y = pt2.y + currTabHt
                    else:
                        tpt1.y = pt1.y - currTabHt
                        tpt2.y = pt2.y - currTabHt
                    tpt1.x = pt1.x + currTabHt/math.tan(math.radians(currTabAngle))
                    tpt2.x = pt2.x - currTabHt/math.tan(math.radians(currTabAngle))
                else: # pt2.x < pt1.x
                    tpt1.y = pt1.y - testHt
                    tpt2.y = pt2.y - testHt
                    tpt1.x = pt1.x - testHt/math.tan(math.radians(testAngle))
                    tpt2.x = pt2.x + testHt/math.tan(math.radians(testAngle))
                    pnpt1 = inkex.paths.Move(tpt1.x, tpt1.y)
                    pnpt2 = inkex.paths.Move(tpt2.x, tpt2.y)
                    if ((not tpath.enclosed) and (self.insidePath(tpath.path, pnpt1) or self.insidePath(tpath.path, pnpt2))) or \
                       (tpath.enclosed and ((not self.insidePath(tpath.path, pnpt1)) and (not self.insidePath(tpath.path, pnpt2)))):
                        tpt1.y = pt1.y + currTabHt
                        tpt2.y = pt2.y + currTabHt
                    else:
                        tpt1.y = pt1.y - currTabHt
                        tpt2.y = pt2.y - currTabHt
                    tpt1.x = pt1.x - currTabHt/math.tan(math.radians(currTabAngle))
                    tpt2.x = pt2.x + currTabHt/math.tan(math.radians(currTabAngle))

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
                        tpt1.y = pt1.y - testHt
                        tpt2.y = pt2.y - testHt
                        tpt1.x = pt1.x + testHt/math.tan(math.radians(testAngle))
                        tpt2.x = pt2.x - testHt/math.tan(math.radians(testAngle))
                        tl1 = [('M', [pt1.x,pt1.y])]
                        tl1 += [('L', [tpt1.x, tpt1.y])]
                        ele1 = inkex.Path(tl1)
                        tl2 = [('M', [pt1.x,pt1.y])]
                        tl2 += [('L', [tpt2.x, tpt2.y])]
                        ele2 = inkex.Path(tl2)
                        thetal1 = ele1.rotate(theta, [pt1.x,pt1.y])
                        thetal2 = ele2.rotate(theta, [pt2.x,pt2.y])
                        tpt1.x = thetal1[1].x
                        tpt1.y = thetal1[1].y
                        tpt2.x = thetal2[1].x
                        tpt2.y = thetal2[1].y
                        pnpt1 = inkex.paths.Move(tpt1.x, tpt1.y)
                        pnpt2 = inkex.paths.Move(tpt2.x, tpt2.y)
                        if ((not tpath.enclosed) and (self.insidePath(tpath.path, pnpt1) or self.insidePath(tpath.path, pnpt2))) or \
                           (tpath.enclosed and ((not self.insidePath(tpath.path, pnpt1)) and (not self.insidePath(tpath.path, pnpt2)))):
                            tpt1.y = pt1.y + currTabHt
                            tpt2.y = pt2.y + currTabHt
                        else:
                            tpt1.y = pt1.y - currTabHt
                            tpt2.y = pt2.y - currTabHt
                        tpt1.x = pt1.x + currTabHt/math.tan(math.radians(currTabAngle))
                        tpt2.x = pt2.x - currTabHt/math.tan(math.radians(currTabAngle))
                        tl1 = [('M', [pt1.x,pt1.y])]
                        tl1 += [('L', [tpt1.x, tpt1.y])]
                        ele1 = inkex.Path(tl1)
                        tl2 = [('M', [pt1.x,pt1.y])]
                        tl2 += [('L', [tpt2.x, tpt2.y])]
                        ele2 = inkex.Path(tl2)
                        thetal1 = ele1.rotate(theta, [pt1.x,pt1.y])
                        thetal2 = ele2.rotate(theta, [pt2.x,pt2.y])
                        tpt1.x = thetal1[1].x
                        tpt1.y = thetal1[1].y
                        tpt2.x = thetal2[1].x
                        tpt2.y = thetal2[1].y
                    else: # pt1.x > pt2.x
                        tpt1.y = pt1.y - testHt
                        tpt2.y = pt2.y - testHt
                        tpt1.x = pt1.x - testHt/math.tan(math.radians(testAngle))
                        tpt2.x = pt2.x + testHt/math.tan(math.radians(testAngle))
                        tl1 = [('M', [pt1.x,pt1.y])]
                        tl1 += [('L', [tpt1.x, tpt1.y])]
                        ele1 = inkex.Path(tl1)
                        tl2 = [('M', [pt1.x,pt1.y])]
                        tl2 += [('L', [tpt2.x, tpt2.y])]
                        ele2 = inkex.Path(tl2)
                        thetal1 = ele1.rotate(theta, [pt1.x,pt1.y])
                        thetal2 = ele2.rotate(theta, [pt2.x,pt2.y])
                        tpt1.x = thetal1[1].x
                        tpt1.y = thetal1[1].y
                        tpt2.x = thetal2[1].x
                        tpt2.y = thetal2[1].y
                        pnpt1 = inkex.paths.Move(tpt1.x, tpt1.y)
                        pnpt2 = inkex.paths.Move(tpt2.x, tpt2.y)
                        if ((not tpath.enclosed) and (self.insidePath(tpath.path, pnpt1) or self.insidePath(tpath.path, pnpt2))) or \
                           (tpath.enclosed and ((not self.insidePath(tpath.path, pnpt1)) and (not self.insidePath(tpath.path, pnpt2)))):
                            tpt1.y = pt1.y + currTabHt
                            tpt2.y = pt2.y + currTabHt
                        else:
                            tpt1.y = pt1.y - currTabHt
                            tpt2.y = pt2.y - currTabHt
                        tpt1.x = pt1.x - currTabHt/math.tan(math.radians(currTabAngle))
                        tpt2.x = pt2.x + currTabHt/math.tan(math.radians(currTabAngle))
                        tl1 = [('M', [pt1.x,pt1.y])]
                        tl1 += [('L', [tpt1.x, tpt1.y])]
                        ele1 = inkex.Path(tl1)
                        tl2 = [('M', [pt1.x,pt1.y])]
                        tl2 += [('L', [tpt2.x, tpt2.y])]
                        ele2 = inkex.Path(tl2)
                        thetal1 = ele1.rotate(theta, [pt1.x,pt1.y])
                        thetal2 = ele2.rotate(theta, [pt2.x,pt2.y])
                        tpt1.x = thetal1[1].x
                        tpt1.y = thetal1[1].y
                        tpt2.x = thetal2[1].x
                        tpt2.y = thetal2[1].y
                else: # slope > 0.0
                    if pt1.x < pt2.x:
                        tpt1.y = pt1.y - testHt
                        tpt2.y = pt2.y - testHt
                        tpt1.x = pt1.x + testHt/math.tan(math.radians(testAngle))
                        tpt2.x = pt2.x - testHt/math.tan(math.radians(testAngle))
                        tl1 = [('M', [pt1.x,pt1.y])]
                        tl1 += [('L', [tpt1.x, tpt1.y])]
                        ele1 = inkex.Path(tl1)
                        tl2 = [('M', [pt1.x,pt1.y])]
                        tl2 += [('L', [tpt2.x, tpt2.y])]
                        ele2 = inkex.Path(tl2)
                        thetal1 = ele1.rotate(theta, [pt1.x,pt1.y])
                        thetal2 = ele2.rotate(theta, [pt2.x,pt2.y])
                        tpt1.x = thetal1[1].x
                        tpt1.y = thetal1[1].y
                        tpt2.x = thetal2[1].x
                        tpt2.y = thetal2[1].y
                        pnpt1 = inkex.paths.Move(tpt1.x, tpt1.y)
                        pnpt2 = inkex.paths.Move(tpt2.x, tpt2.y)
                        if ((not tpath.enclosed) and (self.insidePath(tpath.path, pnpt1) or self.insidePath(tpath.path, pnpt2))) or \
                           (tpath.enclosed and ((not self.insidePath(tpath.path, pnpt1)) and (not self.insidePath(tpath.path, pnpt2)))):
                            tpt1.y = pt1.y + currTabHt
                            tpt2.y = pt2.y + currTabHt
                        else:
                            tpt1.y = pt1.y - currTabHt
                            tpt2.y = pt2.y - currTabHt
                        tpt1.x = pt1.x + currTabHt/math.tan(math.radians(currTabAngle))
                        tpt2.x = pt2.x - currTabHt/math.tan(math.radians(currTabAngle))
                        tl1 = [('M', [pt1.x,pt1.y])]
                        tl1 += [('L', [tpt1.x, tpt1.y])]
                        ele1 = inkex.Path(tl1)
                        tl2 = [('M', [pt1.x,pt1.y])]
                        tl2 += [('L', [tpt2.x, tpt2.y])]
                        ele2 = inkex.Path(tl2)
                        thetal1 = ele1.rotate(theta, [pt1.x,pt1.y])
                        thetal2 = ele2.rotate(theta, [pt2.x,pt2.y])
                        tpt1.x = thetal1[1].x
                        tpt1.y = thetal1[1].y
                        tpt2.x = thetal2[1].x
                        tpt2.y = thetal2[1].y
                    else: # pt1.x > pt2.x
                        tpt1.y = pt1.y - testHt
                        tpt2.y = pt2.y - testHt
                        tpt1.x = pt1.x - testHt/math.tan(math.radians(testAngle))
                        tpt2.x = pt2.x + testHt/math.tan(math.radians(testAngle))
                        tl1 = [('M', [pt1.x,pt1.y])]
                        tl1 += [('L', [tpt1.x, tpt1.y])]
                        ele1 = inkex.Path(tl1)
                        tl2 = [('M', [pt1.x,pt1.y])]
                        tl2 += [('L', [tpt2.x, tpt2.y])]
                        ele2 = inkex.Path(tl2)
                        thetal1 = ele1.rotate(theta, [pt1.x,pt1.y])
                        thetal2 = ele2.rotate(theta, [pt2.x,pt2.y])
                        tpt1.x = thetal1[1].x
                        tpt1.y = thetal1[1].y
                        tpt2.x = thetal2[1].x
                        tpt2.y = thetal2[1].y
                        pnpt1 = inkex.paths.Move(tpt1.x, tpt1.y)
                        pnpt2 = inkex.paths.Move(tpt2.x, tpt2.y)
                        if ((not tpath.enclosed) and (self.insidePath(tpath.path, pnpt1) or self.insidePath(tpath.path, pnpt2))) or \
                           (tpath.enclosed and ((not self.insidePath(tpath.path, pnpt1)) and (not self.insidePath(tpath.path, pnpt2)))):
                            tpt1.y = pt1.y + currTabHt
                            tpt2.y = pt2.y + currTabHt
                        else:
                            tpt1.y = pt1.y - currTabHt
                            tpt2.y = pt2.y - currTabHt
                        tpt1.x = pt1.x - currTabHt/math.tan(math.radians(currTabAngle))
                        tpt2.x = pt2.x + currTabHt/math.tan(math.radians(currTabAngle))
                        tl1 = [('M', [pt1.x,pt1.y])]
                        tl1 += [('L', [tpt1.x, tpt1.y])]
                        ele1 = inkex.Path(tl1)
                        tl2 = [('M', [pt1.x,pt1.y])]
                        tl2 += [('L', [tpt2.x, tpt2.y])]
                        ele2 = inkex.Path(tl2)
                        thetal1 = ele1.rotate(theta, [pt1.x,pt1.y])
                        thetal2 = ele2.rotate(theta, [pt2.x,pt2.y])
                        tpt1.x = thetal1[1].x
                        tpt1.y = thetal1[1].y
                        tpt2.x = thetal2[1].x
                        tpt2.y = thetal2[1].y
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

    def effect(self):
        #START
        #input variables
        
        roof_options = 'no_dormer'
        dormer_height= float(self.options.dormer_height) 


        scale = self.svg.unittouu('1'+self.options.unit)
        if  math.isclose(dormer_height,0,abs_tol=1e-09):
            dormer_height = 0.00000000
            is_dormer = False
        else:
            dormer_height = dormer_height * scale
            roof_options="dormer"
            is_dormer = True
        roof_base_width=float(self.options.roof_base_width) * scale
        roof_base_depth=float(self.options.roof_base_depth) * scale
        roof_peak_ht = float(self.options.roof_peak_ht) * scale
        roof_inset=float(self.options.roof_inset)
        if math.isclose(roof_inset,0):
            roof_inset = 0.000

        if math.isclose(roof_inset,0,abs_tol=1e-09):
            roof_inset = 0.000
            no_inset = True
        else:
            roof_inset= roof_inset * scale
            no_inset = False

        barntype=int(self.options.barn_type) #this is 0 or 1 do not scale
        barnratio=float(self.options.barn_ratio) #percentage, don't scale
        barndepthratio=float(self.options.barn_depth_ratio) #percentage, don't scale
        if roof_options=='dormer':
            #get dormer params

            dormer_width= float(self.options.dormer_width) * scale
            dormer_poly_sides= float(self.options.dormer_poly_sides)
            peakdown = float(self.options.peak_down)*scale  
            nobase = int(self.options.no_base) #this is 0 or 1 do not scale
            extendbase = float(self.options.extend_base)
            if  math.isclose(extendbase,0,abs_tol=1e-09):
                extendbase = 0.00000000
                is_extended = False
            else:
                extendbase = extendbase * scale
                is_extended = True
            inset_ratio = float(self.options.window_frame)  #percentage don't scale
    
        
        layer = self.svg.get_current_layer()
        tabht = 0.4*scale
        taba = 45.0
        dashlength = 0.1*scale
        maxedge = 1 *scale
        #barnratio = .2
        #barndepthratio = .5
        fpath=pathStruct() #dormer front/inset path
        fpath.enclosed = True
        fpath1=pathStruct() #dormre front path saved
        dsidepath=pathStruct() #dormer side piece
        roofpath = pathStruct() #roof main piece
        roofsidepath = pathStruct() #roof side piece
        roofbottompath1 = pathStruct() #roof inner bottom piece (joined path)
        roofbottompath1.enclosed = True
        roofbottompath2 = pathStruct() #roof outer bottom piece (joined path)
        dormerholepath = pathStruct()   #roof hole piece
        dormerholepath1 = pathStruct()
        halfdepth=.5*roof_base_depth
        roof_actual_ht = self.geo_a_b_c(roof_peak_ht, halfdepth)
        inset_slant=math.sqrt(((roof_actual_ht**2)+(roof_inset**2)) - ((2*roof_actual_ht*roof_inset) * math.cos(math.radians(90))))
        roof_inset_ht = self.geo_a_b_c(roof_actual_ht,roof_inset)
        if no_inset:
            side_inset_ht = roof_peak_ht
        else :
            side_inset_ht = self.geo_c_a_b(roof_inset_ht, halfdepth)


        #MAIN ROOF

        #calculate the tilt of the roof from the front to the peak
        base_angle = self.geo_a_b_alpha(roof_peak_ht, halfdepth)
        roof_top_width = roof_base_width-(2*roof_inset)

        #Main Roof
        rpscore = ''
        #start at upper left
        if barntype == 0:
            roofpath.path.append(inkex.paths.Move(roof_inset,0)) #index 0
            roofpath.path.append(inkex.paths.Line((roof_inset+roof_top_width),0))#index 1
            roofpath.path.append(inkex.paths.Line((roof_base_width),roof_actual_ht))#index 2
            roofpath.path.append(inkex.paths.Line(0,roof_actual_ht))#index 3
            roofpath.path.append(inkex.paths.Line(roof_inset,0))#index 4 back to origin
            
        else:
            #variables for barn type
            barn_top_h = barndepthratio*halfdepth
            barn_top_v = roof_peak_ht * barnratio
            barn_top_ln = self.geo_a_b_c(barn_top_h,barn_top_v)
            barn_bottom_h = halfdepth-barn_top_h
            barn_bottom_v = roof_peak_ht-barn_top_v
            barn_bottom_ln = self.geo_a_b_c(barn_bottom_v,barn_bottom_h)
            barn_bottom_y = barn_top_ln + barn_bottom_ln
            
            #barns will ignore inset
            #total of 6 nodes for barn type roof
            roofpath.path.append(inkex.paths.Move(0,0)) #index 0
            roofpath.path.append(inkex.paths.Line(roof_base_width,0)) #index 1
            roofpath.path.append(inkex.paths.Line((roof_base_width),barn_top_ln)) #index 2
            roofpath.path.append(inkex.paths.Line(roof_base_width,barn_bottom_y)) #index 3
            roofpath.path.append(inkex.paths.Line(0,barn_bottom_y)) #index 4
            roofpath.path.append(inkex.paths.Line(0,barn_top_ln)) #index 5
            roofpath.path.append(inkex.paths.Line(0,0)) #index 6 back to origin
              
        # Create the model and scorelines if not barn style
        if barntype == 0:
            roofpathstring = 'M '+ str(roofpath.path[0].x) + ', '+str(roofpath.path[0].y)
            tabpt1, tabpt2 = self.makeTab(roofpath, roofpath.path[0], roofpath.path[1], tabht, taba)
            roofpathstring +=' L '+str(tabpt1.x)+','+str(tabpt1.y)
            roofpathstring +=' L '+str(tabpt2.x)+','+str(tabpt2.y)
            rpscore += self.makescore(roofpath.path[0], roofpath.path[1],dashlength)
            roofpathstring += ' L '+str(roofpath.path[1].x) + ', '+str(roofpath.path[1].y)
            roofpathstring += ' L '+str(roofpath.path[2].x) + ', '+str(roofpath.path[2].y)
            tabpt1, tabpt2 = self.makeTab(roofpath, roofpath.path[2], roofpath.path[3], tabht, taba)
            roofpathstring +=' L '+str(tabpt1.x)+','+str(tabpt1.y)
            roofpathstring +=' L '+str(tabpt2.x)+','+str(tabpt2.y)
            rpscore += self.makescore(roofpath.path[2], roofpath.path[3],dashlength)
            roofpathstring += ' L '+str(roofpath.path[3].x) + ', '+str(roofpath.path[3].y)
            roofpathstring += ' Z'
        else: # is barn type have 5 points in path
            roofpathstring = 'M '+ str(roofpath.path[0].x) + ', '+str(roofpath.path[0].y)
            tabpt1, tabpt2 = self.makeTab(roofpath, roofpath.path[0], roofpath.path[1], tabht, taba)
            roofpathstring +=' L '+str(tabpt1.x)+','+str(tabpt1.y)
            roofpathstring +=' L '+str(tabpt2.x)+','+str(tabpt2.y)
            rpscore += self.makescore(roofpath.path[0], roofpath.path[1],dashlength)
            roofpathstring += ' L '+str(roofpath.path[1].x) + ', '+str(roofpath.path[1].y)
            roofpathstring += ' L '+str(roofpath.path[2].x) + ', '+str(roofpath.path[2].y)
            roofpathstring += ' L '+str(roofpath.path[3].x) + ', '+str(roofpath.path[3].y)
            tabpt1, tabpt2 = self.makeTab(roofpath, roofpath.path[3], roofpath.path[4], tabht, taba)
            roofpathstring +=' L '+str(tabpt1.x)+','+str(tabpt1.y)
            roofpathstring +=' L '+str(tabpt2.x)+','+str(tabpt2.y)
            rpscore += self.makescore(roofpath.path[3], roofpath.path[4],dashlength)
            roofpathstring += ' L '+str(roofpath.path[4].x) + ', '+str(roofpath.path[4].y)
            rpscore += self.makescore(roofpath.path[2], roofpath.path[5],dashlength)
            roofpathstring += ' L '+str(roofpath.path[5].x) + ', '+str(roofpath.path[5].y)
            roofpathstring += ' Z'

        group = inkex.elements._groups.Group()
        group.label = 'g_roofpath1ms'
        self.drawline(roofpathstring, 'roofpath1m', group, sstr="fill:#ffdddd;stroke:#000000;stroke-width:0.25")
        self.drawline(rpscore, 'roofpath1s', group, sstr="fill:#ffdddd;stroke:#000000;stroke-width:0.25")
        group.set('transform','translate('+str(9*scale)+ ','+ str(6*scale) +')')
        layer.append(group)
        # Now create the wrapper if not barntype
        if barntype == 0:
            roofpathstring = 'M '+ str(roofpath.path[0].x) + ', '+str(roofpath.path[0].y)
            roofpathstring += ' L '+str(roofpath.path[1].x) + ', '+str(roofpath.path[1].y)
            roofpathstring += ' L '+str(roofpath.path[2].x) + ', '+str(roofpath.path[2].y)
            roofpathstring += ' L '+str(roofpath.path[3].x) + ', '+str(roofpath.path[3].y)
            roofpathstring += ' Z'
            
            rpe= inkex.PathElement(d=roofpathstring)
            rpe2 = inkex.PathElement(d=roofpathstring)
            
            rpe.set('transform','translate('+str(1*scale)+ ','+ str(4*scale) +')')
            rpe.apply_transform()
            self.drawline(rpe.get('d'), 'roofpath1wms', layer, sstr="fill:#ccffff;stroke:#000000;stroke-width:0.25")
            
            rpe2.set('transform','translate('+str(1*scale)+ ','+ str(9*scale) +')')
            rpe2.apply_transform()
            self.drawline(rpe2.get('d'), 'roofpath2wms', layer, sstr="fill:#ccffff;stroke:#000000;stroke-width:0.25")
            
            
    
            
        else:  #is barntype
            roofpathstring = 'M '+ str(roofpath.path[0].x) + ', '+str(roofpath.path[0].y)
            roofpathstring += ' L '+str(roofpath.path[1].x) + ', '+str(roofpath.path[1].y)
            roofpathstring += ' L '+str(roofpath.path[2].x) + ', '+str(roofpath.path[2].y)
            roofpathstring += ' L '+str(roofpath.path[3].x) + ', '+str(roofpath.path[3].y)
            roofpathstring += ' L '+str(roofpath.path[4].x) + ', '+str(roofpath.path[4].y)
            roofpathstring += ' L '+str(roofpath.path[5].x) + ', '+str(roofpath.path[5].y)
            roofpathstring += ' Z'
        
        ######put pieces and respective scorelines together in groups
            group = inkex.elements._groups.Group()
            group.label = 'g_roofpath1wms'
            self.drawline(roofpathstring, 'roofpath1wms', group, sstr="fill:#ccffff;stroke:#000000;stroke-width:0.25")
            self.drawline(rpscore, 'roofpath1ws', group, sstr="fill:#ccffff;stroke:#000000;stroke-width:0.25")
            group.set('transform','translate('+str(1*scale)+ ','+ str(4*scale) +')')
            layer.append(group)
        
            group = inkex.elements._groups.Group()
            group.label = 'g_roofpath2wms'
            self.drawline(roofpathstring, 'roofpath2wms', group, sstr="fill:#ccffff;stroke:#000000;stroke-width:0.25")
            self.drawline(rpscore, 'roofpath2ws', group, sstr="fill:#ccffff;stroke:#000000;stroke-width:0.25")
            group.set('transform','translate('+str(1*scale)+ ','+ str(8*scale) +')')
            layer.append(group)
        
        rpscore = ''
        #now do a copy of the roof without the top tab only bottom
        if barntype == 0:
            roofpathstring = 'M '+ str(roofpath.path[0].x) + ', '+str(roofpath.path[0].y)
            roofpathstring += ' L '+str(roofpath.path[1].x) + ', '+str(roofpath.path[1].y)
            roofpathstring += ' L '+str(roofpath.path[2].x) + ', '+str(roofpath.path[2].y)
            tabpt1, tabpt2 = self.makeTab(roofpath, roofpath.path[2], roofpath.path[3],tabht, taba)
            roofpathstring +=' L '+str(tabpt1.x)+','+str(tabpt1.y)
            roofpathstring +=' L '+str(tabpt2.x)+','+str(tabpt2.y)
            rpscore += self.makescore(roofpath.path[2], roofpath.path[3],dashlength)
            roofpathstring += ' L '+str(roofpath.path[3].x) + ', '+str(roofpath.path[3].y)
            roofpathstring += ' Z'
            
            
        else: #barntype 
            roofpathstring = 'M '+ str(roofpath.path[0].x) + ', '+str(roofpath.path[0].y)
            roofpathstring += ' L '+str(roofpath.path[1].x) + ', '+str(roofpath.path[1].y)
            roofpathstring += ' L '+str(roofpath.path[2].x) + ', '+str(roofpath.path[2].y)
            roofpathstring += ' L '+str(roofpath.path[3].x) + ', '+str(roofpath.path[3].y)
            tabpt1, tabpt2 = self.makeTab(roofpath, roofpath.path[3], roofpath.path[4],tabht, taba)
            roofpathstring +=' L '+str(tabpt1.x)+','+str(tabpt1.y)
            roofpathstring +=' L '+str(tabpt2.x)+','+str(tabpt2.y)
            rpscore += self.makescore(roofpath.path[3], roofpath.path[4],dashlength)
            roofpathstring += ' L '+str(roofpath.path[4].x) + ', '+str(roofpath.path[4].y)
            roofpathstring += ' L '+str(roofpath.path[5].x) + ', '+str(roofpath.path[5].y)
            rpscore += self.makescore(roofpath.path[2], roofpath.path[5],dashlength)
            roofpathstring += ' Z'
        

        group = inkex.elements._groups.Group()
        group.label = 'g_roofpath2ms'
        self.drawline(roofpathstring, 'roofpath2m', group, sstr="fill:#ffdddd;stroke:#000000;stroke-width:0.25")
        self.drawline(rpscore, 'roofpath2s', group, sstr="fill:#ffdddd;stroke:#000000;stroke-width:0.25")
        group.set('transform','translate('+str(9*scale)+ ','+ str(1*scale) +')')
        layer.append(group)

        #Side of roof
        #From lower left
        #if it is a barntype then we have to add nodes.
        #follow 
        if barntype==0:
            roofsidepath.path.append(inkex.paths.Move(0,0))     
            roofsidepath.path.append(inkex.paths.Line(halfdepth,side_inset_ht))
            roofsidepath.path.append(inkex.paths.Line(-halfdepth,side_inset_ht))
            roofsidepath.path.append(inkex.paths.Line(0,0))
            rpscore = ''
            # Create the model and scorelines
            roofsidepathstring = 'M '+ str(roofsidepath.path[0].x) + ', '+str(roofsidepath.path[0].y)
            tabpt1, tabpt2 = self.makeTab(roofsidepath, roofsidepath.path[0], roofsidepath.path[1],tabht, taba)
            roofsidepathstring +=' L '+str(tabpt1.x)+','+str(tabpt1.y)
            roofsidepathstring +=' L '+str(tabpt2.x)+','+str(tabpt2.y)
            rpscore += self.makescore(roofsidepath.path[0], roofsidepath.path[1],dashlength)
            roofsidepathstring += ' L '+str(roofsidepath.path[1].x) + ', '+str(roofsidepath.path[1].y)
            tabpt1, tabpt2 = self.makeTab(roofsidepath, roofsidepath.path[1], roofsidepath.path[2],tabht, taba)
            roofsidepathstring +=' L '+str(tabpt1.x)+','+str(tabpt1.y)
            roofsidepathstring +=' L '+str(tabpt2.x)+','+str(tabpt2.y)
            rpscore += self.makescore(roofsidepath.path[1], roofsidepath.path[2],dashlength)
            roofsidepathstring += ' L '+str(roofsidepath.path[2].x) + ', '+str(roofsidepath.path[1].y)
            tabpt1, tabpt2 = self.makeTab(roofsidepath, roofsidepath.path[2], roofsidepath.path[3],tabht, taba)
            roofsidepathstring +=' L '+str(tabpt1.x)+','+str(tabpt1.y)
            roofsidepathstring +=' L '+str(tabpt2.x)+','+str(tabpt2.y)
            rpscore += self.makescore(roofsidepath.path[2], roofsidepath.path[3],dashlength)
            roofsidepathstring += ' Z'
            
        else: #this is a barn type roof  -- we will ignore insets for barn type
           
            rpscore =''
            roofsidepath.path.append(inkex.paths.Move(0,0))  #index 0
            roofsidepath.path.append(inkex.paths.Line(barn_top_h,barn_top_v))         #index 1   too short if inset 
            roofsidepath.path.append(inkex.paths.Line(halfdepth,roof_peak_ht)) #index 2
            roofsidepath.path.append(inkex.paths.Line(-halfdepth,roof_peak_ht)) #index 3
            roofsidepath.path.append(inkex.paths.Line(-barn_top_h,barn_top_v)) #index 4
            roofsidepath.path.append(inkex.paths.Line(0,0)) #back to origin index 5
            rpscore = ''
            # Create the model and scorelines
            roofsidepathstring = 'M '+ str(roofsidepath.path[0].x) + ', '+str(roofsidepath.path[0].y)
            tabpt1, tabpt2 = self.makeTab(roofsidepath, roofsidepath.path[0], roofsidepath.path[1],tabht, taba)
            roofsidepathstring +=' L '+str(tabpt1.x)+','+str(tabpt1.y)
            roofsidepathstring +=' L '+str(tabpt2.x)+','+str(tabpt2.y)
            rpscore += self.makescore(roofsidepath.path[0], roofsidepath.path[1],dashlength)
            roofsidepathstring += ' L '+str(roofsidepath.path[1].x) + ', '+str(roofsidepath.path[1].y)
            tabpt1, tabpt2 = self.makeTab(roofsidepath, roofsidepath.path[1], roofsidepath.path[2],tabht, taba)
            roofsidepathstring +=' L '+str(tabpt1.x)+','+str(tabpt1.y)
            roofsidepathstring +=' L '+str(tabpt2.x)+','+str(tabpt2.y)
            rpscore += self.makescore(roofsidepath.path[1], roofsidepath.path[2],dashlength)
            roofsidepathstring += ' L '+str(roofsidepath.path[2].x) + ', '+str(roofsidepath.path[2].y)
            tabpt1, tabpt2 = self.makeTab(roofsidepath, roofsidepath.path[2], roofsidepath.path[3],tabht, taba)
            roofsidepathstring +=' L '+str(tabpt1.x)+','+str(tabpt1.y)
            roofsidepathstring +=' L '+str(tabpt2.x)+','+str(tabpt2.y)
            rpscore += self.makescore(roofsidepath.path[2], roofsidepath.path[3],dashlength)
            
            roofsidepathstring += ' L '+str(roofsidepath.path[3].x) + ', '+str(roofsidepath.path[3].y)
            tabpt1, tabpt2 = self.makeTab(roofsidepath, roofsidepath.path[3], roofsidepath.path[4],tabht, taba)
            roofsidepathstring +=' L '+str(tabpt1.x)+','+str(tabpt1.y)
            roofsidepathstring +=' L '+str(tabpt2.x)+','+str(tabpt2.y)
            rpscore += self.makescore(roofsidepath.path[3], roofsidepath.path[4],dashlength)

            roofsidepathstring += ' L '+str(roofsidepath.path[4].x) + ', '+str(roofsidepath.path[4].y)
            tabpt1, tabpt2 = self.makeTab(roofsidepath, roofsidepath.path[4], roofsidepath.path[5],tabht, taba)
            roofsidepathstring +=' L '+str(tabpt1.x)+','+str(tabpt1.y)
            roofsidepathstring +=' L '+str(tabpt2.x)+','+str(tabpt2.y)
            rpscore += self.makescore(roofsidepath.path[4], roofsidepath.path[5],dashlength)
            roofsidepathstring += ' Z'
            #group = inkex.elements._groups.Group()
            #group.label = 'g_roofsidepath1'
        
        thispathstring = roofsidepathstring + ' ' + rpscore
        self.drawline(thispathstring, 'roofsidepath1', layer, sstr="fill:#ffdddd;stroke:#000000;stroke-width:0.25")
        
        self.drawline(thispathstring, 'roofsidepath2', layer, sstr="fill:#ffdddd;stroke:#000000;stroke-width:0.25")
        
        # Now the wrappers
        roofsidepathstring = 'M '+ str(roofsidepath.path[0].x) + ', '+str(roofsidepath.path[0].y)
        roofsidepathstring += ' L '+str(roofsidepath.path[1].x) + ', '+str(roofsidepath.path[1].y)
        roofsidepathstring += ' L '+str(roofsidepath.path[2].x) + ', '+str(roofsidepath.path[2].y)
        if barntype == 1:
            roofsidepathstring += ' L '+str(roofsidepath.path[3].x) + ', '+str(roofsidepath.path[3].y)
            roofsidepathstring += ' L '+str(roofsidepath.path[4].x) + ', '+str(roofsidepath.path[4].y)
        roofsidepathstring += ' Z'
        self.drawline(roofsidepathstring, 'roofsidepath1w', layer, sstr="fill:#ccffff;stroke:#000000;stroke-width:0.25")
        self.drawline(roofsidepathstring, 'roofsidepath2w', layer, sstr="fill:#ccffff;stroke:#000000;stroke-width:0.25")


        # bottom of the roof
        edge= (.25 * self.options.roof_base_depth)*scale
        if edge > maxedge :
            edge = maxedge
        roofbottompath1.path.append(inkex.paths.Move(edge,edge))
        roofbottompath1.path.append(inkex.paths.Line((roof_base_width - edge),edge))
        roofbottompath1.path.append(inkex.paths.Line((roof_base_width - edge),(roof_base_depth - edge)))
        roofbottompath1.path.append(inkex.paths.Line(edge,(roof_base_depth- edge)))
        roofbottompath1.path.append(inkex.paths.Line(edge,edge))

        roofbottompath2.path.append(inkex.paths.Move(roof_base_width,0))
        roofbottompath2.path.append(inkex.paths.Line(roof_base_width,roof_base_depth))
        roofbottompath2.path.append(inkex.paths.Line(0,roof_base_depth))
        roofbottompath2.path.append(inkex.paths.Line(0,0))
        roofbottompath2.path.append(inkex.paths.Line(roof_base_width,0))
        roofbottompath2.path.reverse()                      
        roofbottompathstring = 'M '+ str(roofbottompath1.path[0].x) + ', '+str(roofbottompath1.path[0].y)
                              
        for nd in range(1,4):
           roofbottompathstring += ' L '+str(roofbottompath1.path[nd].x) + ', '+str(roofbottompath1.path[nd].y)
        roofbottompathstring += ' Z '
        roofbottompathstring += 'M '+ str(roofbottompath2.path[0].x) + ', '+str(roofbottompath2.path[0].y)
        for nd in range(1,4):
           roofbottompathstring += ' L '+str(roofbottompath2.path[nd].x) + ', '+str(roofbottompath2.path[nd].y)
        roofbottompathstring += ' Z'
        
        self.drawline(roofbottompathstring, 'roofbottompath', layer, sstr="fill:#ffdddd;stroke:#000000;stroke-width:0.25")


        if  is_dormer == True:
           #DORMERS  
           
           #input variables:
           #dormer_height is the full height of the dormer as seen from front
           #dormer_width
           #dormer_poly_sides
           #dormer_base_ht is the height of just the base without the polygon top
           #if this is a a barntype then we need to adjust the base angle

           dholepath = []
           dormer_outset = 0.02 *scale
           dormer_angle = 90-base_angle  #for any dormers
           poly_side_ln = 0 #initialize
           edges_in_play = 0 #initialize
           dormer_half_width= dormer_width/2 
           dormer_base_height=dormer_height-(.5*dormer_width)
           dormer_ht_sideview  =  dormer_base_height  #start with the height equal to no polygon top
           dormer_strip_height = dormer_base_height   #start with the height equal to no polygon top
           peaky=0
           peakx=0
           w_peaky=0
           w_peakx=0
           if nobase:
              dormer_base_height = 0
           if dormer_poly_sides>0:
                poly_side_ln  = (dormer_width) * math.sin(math.pi/dormer_poly_sides)  #get the length of the polygon side
                edges_in_play  = dormer_poly_sides /4  #this is how many sides we use to form the dormer side strip
                nominal_peaky = dormer_half_width
                peaky = dormer_half_width
                if dormer_poly_sides == 4:
                #sanity check make sure it is not higher than roof_peak_ht or lower than its nominal height
                    if peakdown> nominal_peaky:
                        peakdown = nominal_peaky+.001  #retain a minimal amount
                    if peaky-peakdown > roof_peak_ht:
                        peakdown = -(roof_peak_ht - nominal_peaky);
                    peaktemp=peaky-peakdown
                    baseup = peaky-peaktemp
                    dormer_base_height += baseup
                    peaky = peaktemp
                w_peaky = self.geo_a_alpha_c(peaky,base_angle)
                #w_peaky = peaky/(math.cos(math.radians(base_angle)))
           #outdent_vtop = self.geo_a_alpha_b(dormer_height,base_angle)
           outdent_vtop= math.sqrt((dormer_height/math.sin(math.radians(base_angle)))**2-dormer_height**2)  #no polygon by default
           nodex_base_top = outdent_vtop
           nodey_base_top = dormer_base_height  

           basetop = dormer_base_height
           basebottom_outdent= 0 


           #only calulate angles if there is a polygon involved

           #if dormer_poly_sides=12 use 75,45 second and  third intervening points then dormer_height at 0
           #if dormer_poly_sides=8 use 67.5 and 22.5 for second intervening point then dormer_height at 0
           #if dormer_poly_sides 4 use dormer_height  no other points just use dormer_height at 0
           stretchbase = self.geo_a_alpha_c(dormer_base_height,base_angle)
           #stretchbase = dormer_base_height/math.cos(math.radians(base_angle))
           dormer_angle = 90 - base_angle #these calculation are on the "outside" of the roof angle
           tv3 = dormer_height
           tvbase = dormer_base_height
           outdent_v1 = 0 # initialize
           outdent_v2 = 0 # initialize
           outdent_v3 = 0
           outdent_base = self.geo_a_alpha_b(dormer_base_height,base_angle)
           halftab = [1,3]
           if dormer_poly_sides == 12: 
              #two intervening points to peak
              pangle1=75
              pangle2=45
              pangle3 = 15
              # ht_sv is used for the dormer front,and to calculate side piece and hole piece
              ht_sv1 = self.geo_c_alpha_a(poly_side_ln,pangle1)
              ht_sv2 = self.geo_c_alpha_a(poly_side_ln,pangle2)
              ht_sv3 = self.geo_c_alpha_a(poly_side_ln,pangle3)
              
              d_fvx_1 = self.geo_c_a_b(poly_side_ln,ht_sv1)
              d_fvx_2 = self.geo_c_a_b(poly_side_ln,ht_sv2)
              d_fvx_3 = self.geo_c_a_b(poly_side_ln,ht_sv3)
        
              #tv values are used for side shapes only
              tv1 = ht_sv1 + dormer_base_height  #this is the summed values the actual y value
              tv2 = tv1 + ht_sv2
              tv3 = tv2 + ht_sv3
              
              #outdents are used for forming the side shape -- how far out from the roof will these points be?
              outdent_v1 = self.geo_a_alpha_b(tv1,base_angle)
              outdent_v2 = self.geo_a_alpha_b(tv2,base_angle)
              outdent_v3 = self.geo_a_alpha_b(tv3,base_angle)
              
                            
              ## holes
              hole_yval_1 = self.geo_a_alpha_c(ht_sv1,base_angle)
              hole_yval_2 = self.geo_a_alpha_c(ht_sv2,base_angle)
              hole_yval_3 = self.geo_a_alpha_c(ht_sv3,base_angle)
              
              #short tabs
              halftab[0] = 4
              halftab[1] = 6

           if dormer_poly_sides == 8: 
              #two intervening points to peak
              pangle1=67.5
              pangle2=22.5
              #for the side piece shape and hole calcs
              ht_sv1 = self.geo_c_alpha_a(poly_side_ln,pangle1)
              ht_sv2 = self.geo_c_alpha_a(poly_side_ln,pangle2)
              tv1 = ht_sv1+dormer_base_height  
              tv2 = tv1+ ht_sv2
              outdent_v1 = self.geo_a_alpha_b(tv1,base_angle)
              outdent_v2 = self.geo_a_alpha_b(tv2,base_angle)
              d_fvx_1 = math.sqrt(poly_side_ln**2 - ht_sv1**2)
              d_fvx_2 = math.sqrt(poly_side_ln**2 - ht_sv2**2)
              hole_yval_1 = self.geo_a_beta_c(ht_sv1,base_angle)
              hole_yval_2 = self.geo_a_beta_c(ht_sv2,base_angle)
              
              halftab[0] = 3
              halftab[1] = 5

           if dormer_poly_sides == 4: 
              #two intervening points to peak
              pangle1= 45
              ht_sv1 = self.geo_c_alpha_a(poly_side_ln,pangle1)
              #ht_sv1  = poly_side_ln*math.sin(math.radians(pangle1))
              
              halftab[0] = 2
              halftab[1] = 4
              
              if peakdown >0 :
                  ht_sv1 = ht_sv1-peakdown # diminish height

              
              tv1 = ht_sv1+dormer_base_height  #this is the incremented value, the actual y value  
              outdent_v1 = self.geo_a_alpha_b(tv1,base_angle)
              d_fvx_1 = math.sqrt(poly_side_ln**2 - ht_sv1**2)
              hole_yval_1 = self.geo_a_beta_c(ht_sv1,base_angle)

           #finally we associate that accumulated x value with the y value that represents the full side length of the polygon 
           # we do this because our side will curve around to the top along the polygon shape, and each segment will be the length of a polygon side
           nodey_v1  =   nodey_base_top + poly_side_ln 
           nodey_v2 =  (nodey_base_top+2*poly_side_ln )
           nodey_v3  =   (nodey_base_top+(3*poly_side_ln ))

           #our total actual height will be the base height plus the length of the sides * the number of poly pieces in play.
           # we  use this when we draw the shape for our side piece. 
           dormer_strip_height  =  dormer_base_height + edges_in_play*poly_side_ln  #this is the full height of the dormer side strip (1 side)
             
           # form the hole piece which is a stretched version of the frontview
           ht_hole_stretched = dormer_height/math.sin(math.radians(base_angle)) #based on front view    #we stretch each y value to the roof angle and keep the x coordinate ( the  d_fvx_ values)  same rules. 
           #start drawing from peak
           #in the case of no peak (no polygon) then just draw the base
           #d_fvx_ and ht_sv can be used to make the front facing shape (not stretched.)
           dhx=[1,2,3,4,5,6,7,8,9,10]
           dhy=[1,2,3,4,5,6,7,8,9,10]
           shx=[1,2,3,4,5,6,7,8,9,10]
           shy=[1,2,3,4,5,6,7,8,9,10]
           dhx[0] = w_peakx
           dhy[0] = -w_peaky
           shx[0] = peakx
           shy[0] = -peaky
           avals_start = 1
           if dormer_poly_sides >0:
              avals_start = 0
           else:
              avals_start = 1
           anum=1
           avals=5
           if nobase:
               avals = 3
           ###########################
           #set up to draw the hole and front dormer pieces
           if dormer_poly_sides==12:
              wyloc3= w_peaky - hole_yval_3
              wyloc2 = wyloc3 - hole_yval_2
              syloc3= peaky - ht_sv3
              syloc2 = syloc3 - ht_sv2
              #assign to array -- first hole
              dhx[1] = d_fvx_3
              dhy[1] = -wyloc3
              dhx[2] = d_fvx_3 + d_fvx_2 ###
              dhy[2] = -wyloc2
              anum=3
              if nobase:
                  nextval = 2
              else:
                  nextval = 4
              dhx[nextval+anum] = -(d_fvx_3 +d_fvx_2)
              dhy[nextval+anum]= -wyloc2
              dhx[nextval+anum+1] = - d_fvx_3
              dhy[nextval+anum+1]= -wyloc3

              # and  now the frontface shape
              shx[1] = d_fvx_3
              shy[1] = -syloc3
              shx[2] = d_fvx_3 + d_fvx_2
              shy[2] = -syloc2
              anum=3
              if nobase:
                  nextval = 2
              else:
                  nextval = 4
              shx[nextval+anum] = -(d_fvx_3 +d_fvx_2)
              shy[nextval+anum]= -syloc2
              shx[nextval+anum+1] = - d_fvx_3
              shy[nextval+anum+1]= -syloc3
              avals=nextval+anum+2

           ###########################
           if dormer_poly_sides==8:
              wyloc2= w_peaky - hole_yval_2
              syloc2= peaky-ht_sv2
              anum=2

              #assign to array -- first hole
              dhx[1] = d_fvx_2
              dhy[1] = -wyloc2
              anum=2
              if nobase:
                  nextval = 2
              else:
                  nextval = 4
              dhx[nextval+anum] = - d_fvx_2
              dhy[nextval+anum]= -wyloc2

              # and  now the frontface shape
              shx[1] = d_fvx_2
              shy[1] = -syloc2

              shx[nextval+anum] = - d_fvx_2
              shy[nextval+anum]= -syloc2
              avals=nextval+anum+1
           ####################################  

           # Draw around base
           # we start with the top right of the base 
           # if no base then ignore the bottom two base nodes
           #first the hole shape
           if nobase == 0:
               dhx[anum]=dormer_half_width
               dhy[anum]=0
               dhx[anum+1]=dormer_half_width
               dhy[anum+1]=stretchbase
               dhx[anum+2]=-dormer_half_width
               dhy[anum+2]=stretchbase
               dhx[anum+3]=  -dormer_half_width
               dhy[anum+3]= 0
               #now the front shape
               shx[anum]=dormer_half_width
               shy[anum]=0
               shx[anum+1]=dormer_half_width
               shy[anum+1]=dormer_base_height
               shx[anum+2]=-dormer_half_width
               shy[anum+2]= dormer_base_height
               shx[anum+3]=  -dormer_half_width
               shy[anum+3]= 0
               #all of them close back to start
           else:
               dhx[anum]=dormer_half_width
               dhy[anum]=0
               dhx[anum+1]=  -dormer_half_width
               dhy[anum+1]= 0
               
               #now the front shape
               shx[anum]=dormer_half_width
               shy[anum]=0
               shx[anum+1]=  -dormer_half_width
               shy[anum+1]= 0
               
               #all of them close back to start

           fpath.path.append(inkex.paths.Move(shx[avals_start],shy[avals_start]))
           dormerholepath.path.append(inkex.paths.Move(dhx[avals_start],dhy[avals_start]))
           for n in range(avals_start+1,avals):
              fpath.path.append(inkex.paths.Line(shx[n],shy[n]))
              dormerholepath.path.append(inkex.paths.Line(dhx[n],dhy[n]))
              
           fpath.path.append(inkex.paths.Line(shx[avals_start],shy[avals_start]))
           dormerholepath.path.append(inkex.paths.Line(dhx[avals_start],dhy[avals_start]))
           
           #outset it
           dormerholepath1 = copy.deepcopy(dormerholepath)          
           del dormerholepath1.path[-1]       # can't pass the closing point to insetPolygon
           #########################################
           self.insetPolygon(dormerholepath1.path,dormer_outset)
           #######################################       
           #back to string
           
           dormerholepathstring = 'M '+ str(dormerholepath1.path[0].x) + ', '+str(dormerholepath1.path[0].y)
           for nd in range(1,len(dormerholepath1.path)):
                dormerholepathstring += ' L '+str(dormerholepath1.path[nd].x) + ', '+str(dormerholepath1.path[nd].y)
           dormerholepathstring+=' Z'
           self.drawline(dormerholepathstring, 'dormerholepath', layer, sstr="fill:#cccccc;stroke:#000000;stroke-width:0.25")
            #

           #make inset for front window
           window_inset = inset_ratio*dormer_width
           if (window_inset> dormer_half_width) or  (window_inset>.5 * peaky):
             window_inset = inset_ratio * min(dormer_width, peaky) 
           if peaky == 0:
             window_inset = inset_ratio*dormer_width

         
           fpath1 = copy.deepcopy(fpath)
           del fpath.path[-1] # can't pass the closing point to insetPolygon
           #########################################
           self.insetPolygon(fpath.path, -(window_inset))
           #######################################
           fpath.path.append(inkex.paths.Line(fpath.path[0].x, fpath.path[0].y))
           fpath.path.reverse()
           #put fpath into string
           rpscore = ''
           fpathstring = 'M '+ str(fpath.path[0].x) + ', '+str(fpath.path[0].y)
           for nd in range(1,len(fpath.path)):
                fpathstring += ' L '+str(fpath.path[nd].x) + ', '+str(fpath.path[nd].y)
           fpathstring +=' Z'

           fpath1string = 'M '+ str(fpath1.path[0].x) + ', '+str(fpath1.path[0].y)
           for nd in range(1,len(fpath1.path)-1):
                fpath1string += ' L '+str(fpath1.path[nd].x) + ', '+str(fpath1.path[nd].y)
           fpath1string+=' Z'
           self.drawline(fpathstring+' '+fpath1string, 'frontpathw', layer, sstr="fill:#ccffff;stroke:#000000;stroke-width:0.25")
           
           
           #put fpath1 into string
           fpath1.enclosed = False
           fpath1string = 'M '+ str(fpath1.path[0].x) + ', '+str(fpath1.path[0].y)
           
           for nd in range(1,len(fpath1.path)-1): 
                if extendbase < tabht:
                    if ((nd==halftab[0]) or (nd==halftab[1])):
                        tabpt1, tabpt2 = self.makeTab(fpath1, fpath1.path[nd-1], fpath1.path[nd],tabht/2, taba)
                        if nd==halftab[0]:
                            tabpt2.x -= tabht/3
                        else:
                            tabpt1.x += tabht/3 
                    else:
                        tabpt1, tabpt2 = self.makeTab(fpath1, fpath1.path[nd-1], fpath1.path[nd],tabht, taba)   
                else:
                    tabpt1, tabpt2 = self.makeTab(fpath1, fpath1.path[nd-1], fpath1.path[nd],tabht, taba)
                fpath1string +=' L '+str(tabpt1.x)+','+str(tabpt1.y)
                fpath1string +=' L '+str(tabpt2.x)+','+str(tabpt2.y)
                rpscore += self.makescore(fpath1.path[nd-1], fpath1.path[nd],dashlength/2) # put a scoreline across it
                
                fpath1string += ' L '+str(fpath1.path[nd].x) + ', '+str(fpath1.path[nd].y)
             
                    
           tabpt1, tabpt2 = self.makeTab(fpath1, fpath1.path[-2], fpath1.path[-1],tabht, taba) #last tab
           fpath1string +=' L '+str(tabpt1.x)+','+str(tabpt1.y)
           fpath1string +=' L '+str(tabpt2.x)+','+str(tabpt2.y)
           fpath1string+=' Z '
           rpscore += self.makescore(fpath1.path[-2], fpath1.path[-1],dashlength/2) #score line for last tab
           

           inset_window_path = fpath1string+fpathstring+' '+ rpscore
           self.drawline(inset_window_path, 'frontpaths', layer, sstr="fill:#ffdddd;stroke:#000000;stroke-width:0.25")
  

           ##############################################################
           # DORMER SIDE PIECES 
           # draw from top left, then down, then travel up right side v1 v2 v3 counter-clockwise
           
           dside1 = ' M '+ str(-extendbase) + ','+ str(0)
           dsidepath.path.append(inkex.paths.Move(-extendbase,0))
           #begin selective for number of polygon sides on top of dormer
           #FIX if there is an extension it will add 2 nodes to the path add them and adjust the tscire and hscore maps
           # nodes at 0,dormer_strip_height and 0, -dormer_strip_height
           hscoremap = []
           cscoremap = []
           if dormer_poly_sides == 12 :
                #lets put into list
                #extendbase moves zero-point out use -extendbase
                #start at middle left side
                dsidepath.path.append(inkex.paths.Line(-extendbase,ht_sv2))
                dsidepath.path.append(inkex.paths.Line(-extendbase,(ht_sv1+ht_sv2)))
                dsidepath.path.append(inkex.paths.Line(-extendbase,(dormer_strip_height-dormer_base_height)))
                dsidepath.path.append(inkex.paths.Line(-extendbase,dormer_strip_height))
                #FIX first extra here
                if is_extended:
                    dsidepath.path.append(inkex.paths.Line(0,dormer_strip_height))
                #lower right side
                dsidepath.path.append(inkex.paths.Line(outdent_base,(dormer_strip_height-dormer_base_height)))
                dsidepath.path.append(inkex.paths.Line(outdent_v1,(ht_sv1+ht_sv2)))
                dsidepath.path.append(inkex.paths.Line(outdent_v2,(ht_sv2)))
                dsidepath.path.append(inkex.paths.Line(outdent_v3,0))
                #now upper right side
                dsidepath.path.append(inkex.paths.Line(outdent_v2,-(ht_sv2)))
                dsidepath.path.append(inkex.paths.Line(outdent_v1,-(ht_sv1+ht_sv2)))
                dsidepath.path.append(inkex.paths.Line(outdent_base,-(dormer_strip_height-dormer_base_height)))
                if is_extended:
                    dsidepath.path.append(inkex.paths.Line(0,-dormer_strip_height))
                dsidepath.path.append(inkex.paths.Line(-extendbase,-dormer_strip_height)) #at top
                #back down left side from top
                dsidepath.path.append(inkex.paths.Line(-extendbase,-(dormer_strip_height-dormer_base_height))) #top -1
                dsidepath.path.append(inkex.paths.Line(-extendbase,-(ht_sv1+ht_sv2))) #top -2
                dsidepath.path.append(inkex.paths.Line(-extendbase,-(ht_sv2))) #top -3
                dsidepath.path.append(inkex.paths.Line(-extendbase,0))
                if is_extended:
                    hscoremap = [6,7,8,9,10,11,12]
                    tscoremap = [6,7,8,9,10,11,12,13]
                    cscoremap = [9]
                else:
                    hscoremap = [5,6,7,8,9,10,11]
                    tscoremap = [5,6,7,8,9,10,11,12]
                    cscoremap = [8]
           if dormer_poly_sides == 8 :
              dsidepath.path.append(inkex.paths.Line(-extendbase,ht_sv1))
              dsidepath.path.append(inkex.paths.Line(-extendbase,(dormer_strip_height-dormer_base_height)))
              dsidepath.path.append(inkex.paths.Line(-extendbase,dormer_strip_height)) #at bottom
              if is_extended:
                    dsidepath.path.append(inkex.paths.Line(0,dormer_strip_height))
                            
              dsidepath.path.append(inkex.paths.Line(outdent_base,(dormer_strip_height-dormer_base_height)))                    
              dsidepath.path.append(inkex.paths.Line(outdent_v1,(ht_sv1)))
              dsidepath.path.append(inkex.paths.Line(outdent_v2,0)) #at mid
              
              dsidepath.path.append(inkex.paths.Line(outdent_v1,-(ht_sv1)))
              dsidepath.path.append(inkex.paths.Line(outdent_base,-(dormer_strip_height-dormer_base_height)))
              if is_extended:
                    dsidepath.path.append(inkex.paths.Line(0,-dormer_strip_height))
              dsidepath.path.append(inkex.paths.Line(-extendbase,-dormer_strip_height) )                                      
              dsidepath.path.append(inkex.paths.Line(-extendbase,-(dormer_strip_height-dormer_base_height)) )                                      
              dsidepath.path.append(inkex.paths.Line(-extendbase,-(ht_sv1)))
              dsidepath.path.append(inkex.paths.Line(-extendbase,0))
              if is_extended:
                  hscoremap = [5,6,7,8,9]
                  tscoremap = [5,6,7,8,9,10]
                  cscoremap = [7]
              else:
                  hscoremap = [4,5,6,7,8]
                  tscoremap = [4,5,6,7,8,9]
                  cscoremap = [6]
              
           if dormer_poly_sides ==4:
              dsidepath.path.append(inkex.paths.Line(-extendbase,(dormer_strip_height-dormer_base_height)))
              dsidepath.path.append(inkex.paths.Line(-extendbase,dormer_strip_height))
              if is_extended:
                    dsidepath.path.append(inkex.paths.Line(0,dormer_strip_height))
              dsidepath.path.append(inkex.paths.Line(outdent_base,(dormer_strip_height-dormer_base_height)))
              dsidepath.path.append(inkex.paths.Line(outdent_v1,0))
              dsidepath.path.append(inkex.paths.Line(outdent_base,-(dormer_strip_height-dormer_base_height)))
              if is_extended:
                    dsidepath.path.append(inkex.paths.Line(0,-dormer_strip_height))
              dsidepath.path.append(inkex.paths.Line(-extendbase,-dormer_strip_height))
              dsidepath.path.append(inkex.paths.Line(-extendbase,-(dormer_strip_height-dormer_base_height)))
              dsidepath.path.append(inkex.paths.Line(-extendbase,0))
              if is_extended:
                  hscoremap = [4,5,6]
                  tscoremap = [4,5,6,7]
                  cscoremap = [5]
              else:
                  hscoremap = [3,4,5]
                  tscoremap = [3,4,5,6]
                  cscoremap = [4]

           if dormer_poly_sides == 0:
              dsidepath.path.append(inkex.paths.Line(-extendbase,(.5*dormer_width)))
              dsidepath.path.append(inkex.paths.Line(-extendbase,(.5*dormer_width+dormer_base_height)))
              dsidepath.path.append(inkex.paths.Line(outdent_base,(.5*dormer_width)))
              dsidepath.path.append(inkex.paths.Line(outdent_base,-(.5*dormer_width)))
              dsidepath.path.append(inkex.paths.Line(-extendbase,-((.5*dormer_width)+dormer_base_height)))
              dsidepath.path.append(inkex.paths.Line(-extendbase,-(.5*dormer_width)))
              dsidepath.path.append(inkex.paths.Line(-extendbase,0))
              tscoremap = [3,4,5]
              hscoremap = [3,4]
              cscoremap =[3,4]
              
              
              
           #wrapper
           rpscore = ''
           dsidepathstring = 'M '+ str(dsidepath.path[0].x) + ', '+str(dsidepath.path[0].y)
           for nd in range(1,len(dsidepath.path)-1):
               dsidepathstring += ' L '+str(dsidepath.path[nd].x) + ', '+str(dsidepath.path[nd].y)
               if nd in cscoremap:
                    # Put a scoreline across the shape
                    otherend = inkex.paths.Line(-extendbase, dsidepath.path[nd].y)
                    rpscore += self.makescore(dsidepath.path[nd], otherend,dashlength/2) # put a scoreline across it     
                    
           dsidepathstring += ' Z'
           dsidepathstring += ' '+ rpscore
           #group = inkex.elements._groups.Group()
           #group.label = 'g_dsidepathws'
           self.drawline(dsidepathstring, 'dsidepathw', layer, sstr="fill:#ccffff;stroke:#000000;stroke-width:0.25")

           
           #start structure using same path
           rpscore = ''
           dsidepathstring = 'M '+ str(dsidepath.path[0].x) + ', '+str(dsidepath.path[0].y)
           for nd in range(1,len(dsidepath.path)-1):
               if dormer_poly_sides >= 0 : 
                   if nd in tscoremap:
                        # Put a tab between this point and the previous one
                        tabpt1, tabpt2 = self.makeTab(dsidepath, dsidepath.path[nd-1], dsidepath.path[nd],tabht, taba)
                        dsidepathstring +=' L '+str(tabpt1.x)+','+str(tabpt1.y)
                        dsidepathstring +=' L '+str(tabpt2.x)+','+str(tabpt2.y)
                        rpscore += self.makescore(dsidepath.path[nd-1], dsidepath.path[nd],dashlength/2) # put a scoreline across it
               dsidepathstring += ' L '+str(dsidepath.path[nd].x) + ', '+str(dsidepath.path[nd].y)
               if dormer_poly_sides >= 0 :
                    if nd in hscoremap:
                        # Put a scoreline across the shape
                        otherend = inkex.paths.Line(-extendbase, dsidepath.path[nd].y)
                        rpscore += self.makescore(dsidepath.path[nd], otherend,dashlength/2) # put a scoreline across it                   
           dsidepathstring += ' Z'
           rpscore += ' Z'
           thispathstring = dsidepathstring+' '+rpscore
           #group = inkex.elements._groups.Group()
           #group.label = 'g_dsidepathms'
           self.drawline(thispathstring, 'dsidepathm', layer, sstr="fill:#ffdddd;stroke:#000000;stroke-width:0.25")


if __name__ == '__main__':
    Roofmaker().run()

