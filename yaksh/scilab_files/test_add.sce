mode(-1)
exec("function.sci",-1);
i = 0
p = add(3,5);
correct = (p == 8);
if correct then
 i=i+1
end
disp("Input submitted 3 and 5")
disp("Expected output 8 got " + string(p))
p = add(22,-20);
correct = (p==2);
if correct then
 i=i+1
end
disp("Input submitted 22 and -20")
disp("Expected output 2 got " + string(p))
p =add(91,0);
correct = (p==91);
if correct then
 i=i+1
end
disp("Input submitted 91 and 0")
disp("Expected output 91 got " + string(p))
if i==3 then
 exit(5);
else
 exit(3);
end
