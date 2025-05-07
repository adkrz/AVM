struct str(byte a, addr b, addr c[5]);
struct additional(str x[2], addr y);

additional zmienna;

function modify_by_global() begin
global zmienna;
zmienna.x[0].a = 5;
end

call modify_by_global();
print zmienna.x[0].a;
printnl;
