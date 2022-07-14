clear
load("../../controller/paper_exp/gke_data.mat")

T=linspace(0,size(NN,2)*5,size(NN,2));

sampling=5;
fontsize=30;

figure('units','normalized','outerposition',[0 0 1 1])
set(gca,'FontSize',fontsize)
hold on
box on
grid on
stairs(T(1:sampling:end)/60,NN(1,1:sampling:end),'LineWidth',1.2);
stairs(T(1:sampling:end)/60,GKEt(1,1:sampling:end),'LineWidth',1.5);
ylim([0,max(NN(1,:))*1.03])
xlim([0,max(T(1:sampling:end)/60)]*1.05)
xlabel("Tempo (min)")
ylabel("#CPUs")
legend('SUDA','VPA')
exportgraphics(gcf,"gkevsmuopt.png")
close()


figure('units','normalized','outerposition',[0 0 1 1])
set(gca,'FontSize',fontsize)
hold on
box on
grid on
stairs(T(1:sampling:end)/60,NN(2,1:sampling:end),'LineWidth',1.2);
stairs(T(1:sampling:end)/60,GKEt(2,1:sampling:end),'LineWidth',1.5);
ylim([0,max(NN(2,:))*1.03])
ylabel("#CPUs")
xlabel("Tempo (min)")
xlim([0,max(T(1:sampling:end)/60)]*1.05)
legend('SUDA','VPA')
exportgraphics(gcf,"gkevsmuopt2.png")
close()

% Z = cumtrapz(T(1:sampling:end),NN(1,1:sampling:end));
% 
% figure
% hold on;
% stairs(T(1:sampling:end),NN(1,1:sampling:end))
% stairs(T(1:sampling:end),Z)

figure('units','normalized','outerposition',[0 0 1 1])
set(gca,'FontSize',fontsize)
hold on
box on
grid on

T2 = [T(1:sampling:end), fliplr(T(1:sampling:end))];
inBetween = [min(NN(1,1:sampling:end),GKEt(1,1:sampling:end)), fliplr(GKEt(1,1:sampling:end))];
fill(T2/60, inBetween, 'yellow','FaceAlpha',0.1,'LineWidth',0.8,'Linestyle','-');

ylim([0,max(NN(1,:))])
ylabel("#CPUs")
xlabel("Tempo (min)")
xlim([0,max(T2/60)]*1.05)
legend('CostoAddVPA')

exportgraphics(gcf,"usedCore.png")
close()


Tnn=trapz(T(1:sampling:end),NN(1,1:sampling:end));
Tgke=trapz(T(1:sampling:end),GKEt(1,1:sampling:end));

