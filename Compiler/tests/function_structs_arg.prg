struct str(byte a, addr b, addr c[5]);
struct additional(str x[2], addr y);

additional zmienna;

function modify_by_ref(additional Z) begin
Z.x[0].a = 5;
end

call modify_by_ref(zmienna);
print zmienna.x[0].a;
printnl;

additional zmienna_tablica[5];

function modify_by_ref2(additional Z[]) begin
Z[2].x[0].a = 6;
end

call modify_by_ref2(zmienna_tablica);
addr index = 2;
print zmienna_tablica[index].x[0].a;
printnl;
