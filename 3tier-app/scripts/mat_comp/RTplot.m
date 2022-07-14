% X0=zeros(1,7);
% MU=zeros(1,7);
% NT=[inf,inf,inf];
% NC=[inf,inf,inf];
% 
% 
% 
% %X(5)=XE2_e;
% %X(6)=XE1_e;
% %X(7)=XBrowse_browse;
% 
% MU([5,6,7])=[10,10,1];
% Xi=100;
% X0(end)=100;
% rep=1;
% TF=60;
% dt=60;
% 
% 
% 
% nsteps=180;
% Client=zeros(1,nsteps);
% Tx=zeros(1,nsteps);
% 
% for i=1:nsteps
%     if(mod(i,20)==0)
%         X0(end)=ceil(X0(end)+randn()*0.15*X0(end));
%     end
%     Client(i)=sum(X0([2,4,5,6,7]));
%     X=lqn(X0,MU,NT,NC,TF,rep,dt);
%     X0=X(1:end-1,end);
%     Tx(i)=X(end,end)/TF;
% end



cumAcgrt=cumsum((Client./Tx)-1)./linspace(1,nsteps,nsteps);
RT=(Client./Tx)-1;

figure('units','normalized','outerposition',[0 0 1 1])
subplot(2,1,1);
fontsize=28;
% figure('units','normalized','outerposition',[0 0 1 1])
set(gca,'FontSize',fontsize) 
hold on;
grid on;
box on;

yline(0.2,"linewidth",1.1)
plot(cumAcgrt,"linestyle","--","linewidth",2.0,"color","b");
stairs(RT,"linewidth",1.1);

ylim([0.1,max(RT)*1.02])

ylabel("Tempo Di Risposta (sec)")
xlabel("Tempo (min)")

legend("TR_{Rif}","Media_{1m}","Media_{t}","location","southEast","Orientation","horizontal");
%exportgraphics(gcf,"RT.png");
%close()

subplot(2,1,2);
% figure('units','normalized','outerposition',[0 0 1 1])
set(gca,'FontSize',fontsize) 
hold on;
grid on;
box on;

stairs(Client,"linewidth",1.4);
ylabel("#Utenti");
xlabel("Tempo (min)");

legend("UtentiAttivi","location","southEast","Orientation","horizontal");
% exportgraphics(gcf,"Utenti.png");
% close()

exportgraphics(gcf,"RT.png");
close()
