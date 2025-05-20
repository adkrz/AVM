struct point(byte x, byte y);
struct point3d(point p, byte z);

function printpt(point3d pt) begin
print "X=";
print pt.p.x;
print " Y=";
print pt.p.y;
print " Z=";
print pt.z;
printnl;
end

point3d pt;
pt.p.x = 11;
pt.p.y = 22;
pt.z = 33;

call printpt(pt);

// Pass sub-struct to another function:

function setxy_only(point pt) begin
pt.x = 44;
pt.y = 55;
end

call setxy_only(pt.p);
call printpt(pt);
