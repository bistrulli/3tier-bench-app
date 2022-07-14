clear
load("../../controller/nn_data.mat");

cumAvg=[];

for i=1:size(sIdx,2)
    fIdx=-1;
    iIdx=sIdx{i}.idx+1;
    if(i==size(sIdx,2))
        fIdx=size(XSSIM,1);
    else
        fIdx=sIdx{i+1}.idx;
    end
    
    cumAvg=[cumAvg, (cumsum(XSSIM(iIdx:fIdx,1))./(linspace(1,double(fIdx-iIdx)+1,double(fIdx-iIdx)+1))')'];
end

T=linspace(0,size(XSSIM,1)/(4*60),size(XSSIM,1));

fontsize=30;
figure('units','normalized','outerposition',[0 0 1 1])
set(gca,'FontSize',fontsize) 
hold on
grid on 
box on
plot(T,cumAvg,"linestyle","--","linewidth",1.1);
stairs(T(1:50:end),XSSIM(1:50:end,1),"linewidth",0.9);
ylabel("#Utenti");
xlabel("Tempo (min)");
legend("MediaCumulativa","MediaUltimoMinuto");
exportgraphics(gcf,"training.png");
close()