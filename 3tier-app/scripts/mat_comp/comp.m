clear
load ../../controller/gke_data.mat

T=linspace(0,size(NN,2),size(NN,2));


figure('units','normalized','outerposition',[0 0 1 1])
hold on
box on
grid on
stairs(T,NN(1,:),'LineWidth',1.2);
stairs(T,GKEt(1,:),'LineWidth',1.5);
legend('Tier1_{NN}','Tier1_{GKE}')


figure('units','normalized','outerposition',[0 0 1 1])
hold on
box on
grid on
stairs(T,NN(2,:),'LineWidth',1.2);
stairs(T,GKEt(2,:),'LineWidth',1.5);
legend('Tier2_{NN}','Tier2_{GKE}')

figure('units','normalized','outerposition',[0 0 1 1])
hold on
box on
grid on
stairs(T,NN(1,:),'LineWidth',1.2);
stairs(T,GKEu(1,:),'LineWidth',1.5);
legend('Tier1_{NN}','Tier1_{GKE}')


figure('units','normalized','outerposition',[0 0 1 1])
hold on
box on
grid on
stairs(T,NN(2,:),'LineWidth',1.2);
stairs(T,GKEu(2,:),'LineWidth',1.5);
legend('Tier2_{NN}','Tier2_{GKE}')

