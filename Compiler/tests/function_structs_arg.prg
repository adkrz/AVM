struct str(byte a, addr b, addr c[5]);
struct additional(str x[2], addr y);

additional zmienna;

function modify_by_ref(additional Z) begin
Z.x[0].a = 5;
end

call modify_by_ref(zmienna);
print zmienna.x[0].a;
printnl;