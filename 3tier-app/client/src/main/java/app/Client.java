package app;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpClient.Version;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.http.HttpResponse.BodyHandlers;
import java.util.UUID;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

import org.apache.commons.math3.distribution.AbstractRealDistribution;
import org.apache.commons.math3.distribution.ExponentialDistribution;

import Server.SimpleTask;
import net.spy.memcached.MemcachedClient;

public class Client implements Runnable {

	private SimpleTask task = null;
	private ExponentialDistribution dist = null;
	private long thinkTime = -1;
	private UUID clietId = null;
	public static AtomicInteger time = new AtomicInteger(0);
	private MemcachedClient memcachedClient = null;
	private static AtomicInteger toKill = new AtomicInteger(0);
	private Boolean dying=null;
	private static String tier1Host=null;
	public static AtomicBoolean isStarted=new AtomicBoolean(false);

	public Client(SimpleTask task, Long ttime) {
		this.setThinkTime(ttime);
		this.task = task;
		this.clietId = UUID.randomUUID();
		this.dying=false;
	}

	public void run() {
		try {
			HttpClient client = null;
			HttpRequest request = null;
			client = HttpClient.newBuilder().version(Version.HTTP_1_1).build();
			request = HttpRequest.newBuilder()
					.uri(URI.create("http://"+Client.getTier1Host()+":3000/?id=" + this.clietId.toString() + "&entry=e1" + "&snd=think"))
					.build();
			
			Client.isStarted.set(true);
			int thinking = this.task.getState().get("think").incrementAndGet();
			
			while (!this.dying) {
				
				SimpleTask.getLogger().debug(String.format("%s thinking", thinking));
				TimeUnit.MILLISECONDS.sleep(Double.valueOf(this.dist.sample()).longValue());

				SimpleTask.getLogger().debug(String.format("%s sending", this.task.getName()));
				this.task.getState().get("think").decrementAndGet();
				HttpResponse<String> resp = client.send(request, BodyHandlers.ofString());
				
				if (Client.getToKill().get() > 0) {
					Client.toKill.decrementAndGet();
					this.dying = true;
				}
				
				thinking = this.task.getState().get("think").incrementAndGet();
			}
			SimpleTask.getLogger().debug(String.format(" user %s stopped", this.clietId));
		} catch (IOException e1) {
			e1.printStackTrace();
		} catch (InterruptedException e2) {
			e2.printStackTrace();
		} catch (Exception e) {
			e.printStackTrace();
		} finally {
			this.memcachedClient.shutdown();
		}
	}

	public long getThinkTime() {
		return this.thinkTime;
	}

	public AbstractRealDistribution getTtimeDist() {
		return this.dist;
	}

	public void setThinkTime(long thinkTime) {
		this.thinkTime = thinkTime;
		this.dist = new ExponentialDistribution(thinkTime);
	}

	public static AtomicInteger getToKill() {
		return toKill;
	}

	public static void setToKill(Integer toKill) {
		Client.toKill.set(toKill);
	}
	
	public static String getTier1Host() {
		return tier1Host;
	}

	public static void setTier1Host(String tier1Host) {
		Client.tier1Host = tier1Host;
	}

}
