package app;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpClient.Version;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse.BodyHandlers;
import java.time.Duration;
import java.util.UUID;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

import org.apache.commons.math3.distribution.AbstractRealDistribution;
import org.apache.commons.math3.distribution.ExponentialDistribution;

import Server.SimpleTask;
import redis.clients.jedis.Jedis;

public class Client implements Runnable {

	private SimpleTask task = null;
	private ExponentialDistribution dist = null;
	private long thinkTime = -1;
	public static AtomicInteger nrq = new AtomicInteger(0);
	private UUID clietId=null;
	public  static AtomicInteger time=new AtomicInteger(0);
	

	public Client(SimpleTask task, Long ttime) {
		this.setThinkTime(ttime);
		this.task=task;
		this.clietId=UUID.randomUUID();
	}

	public void run() {
		try {
			HttpClient client=null;
			HttpRequest request=null;
			client=HttpClient.newBuilder().version(Version.HTTP_1_1).build();
			request=HttpRequest.newBuilder().uri(URI.create("http://localhost:3000/?id="+this.clietId.toString()+"&entry=e1"+"&snd=think")).
					timeout(Duration.ofMinutes(10)).build();
			
			Jedis jedis = this.task.getJedisPool().getResource();
			jedis.incr("think");
			while (!Thread.currentThread().isInterrupted()) { 

				TimeUnit.MILLISECONDS.sleep(Double.valueOf(this.dist.sample()).longValue());
				
				SimpleTask.getLogger().debug(String.format("%s sent",this.task.getName()));
				client.send(request, BodyHandlers.ofString());
				
				jedis.incr("think");
			}
			jedis.close();
		} catch (IOException e1) {
			e1.printStackTrace();
		}
		catch(InterruptedException e2) {
			e2.printStackTrace();
		}
		catch (Exception e) {
			e.printStackTrace();
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
