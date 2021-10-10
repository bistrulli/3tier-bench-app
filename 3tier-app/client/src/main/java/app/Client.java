package app;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpClient.Version;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.http.HttpResponse.BodyHandlers;
import java.util.UUID;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

import org.apache.commons.math3.distribution.AbstractRealDistribution;
import org.apache.commons.math3.distribution.ExponentialDistribution;

import Server.SimpleTask;
import net.spy.memcached.MemcachedClient;

public class Client implements Runnable {

	private SimpleTask task = null;
	private ExponentialDistribution dist = null;
	private long thinkTime = -1;
	public static AtomicInteger nrq = new AtomicInteger(0);
	private UUID clietId = null;
	public static AtomicInteger time = new AtomicInteger(0);
	private MemcachedClient memcachedClient = null;

	public Client(SimpleTask task, Long ttime) {
		this.setThinkTime(ttime);
		this.task = task;
		this.clietId = UUID.randomUUID();
		try {
			this.memcachedClient = new MemcachedClient(new InetSocketAddress(this.task.getJedisHost(), 11211));
		} catch (IOException e) {
			e.printStackTrace();
		}
	}

	public void run() {
		try {
			HttpClient client = null;
			HttpRequest request = null;
			client = HttpClient.newBuilder().version(Version.HTTP_1_1).build();
//			request = HttpRequest.newBuilder()
//					.uri(URI.create("http://tier1:3000/?id=" + this.clietId.toString() + "&entry=e1" + "&snd=think"))
//					.build();

			request = HttpRequest.newBuilder().uri(URI.create("http://www.google.com")).build();

			while (this.memcachedClient.get("stop") == null
					|| !String.valueOf(this.memcachedClient.get("stop")).equals("1")) {

				SimpleTask.getLogger().debug(String.format("stop=%s", String.valueOf(memcachedClient.get("stop"))));
				TimeUnit.MILLISECONDS.sleep(Double.valueOf(this.dist.sample()).longValue());

				SimpleTask.getLogger().debug(String.format("%s sending", this.task.getName()));
				HttpResponse<String> resp = client.send(request, BodyHandlers.ofString());

				long thinking = this.memcachedClient.incr("think", 1);

				SimpleTask.getLogger().debug(String.format("%d thinking", thinking));
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

}
