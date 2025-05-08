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

additional zmienna_tablica[5];

function modify_by_global2() begin
global zmienna_tablica;
zmienna_tablica[2].x[0].a = 6;
end

call modify_by_global2();
print zmienna_tablica[2].x[0].a;
printnl;
