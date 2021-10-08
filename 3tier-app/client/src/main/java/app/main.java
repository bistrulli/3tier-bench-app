package app;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.util.HashMap;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;

import com.google.common.net.InetAddresses;
import com.google.common.net.InternetDomainName;
import com.google.gson.Gson;

import Server.SimpleTask;
import gnu.getopt.Getopt;
import gnu.getopt.LongOpt;
import net.spy.memcached.MemcachedClient;
import net.spy.memcached.internal.OperationFuture;
import redis.clients.jedis.Jedis;
import redis.clients.jedis.Transaction;

public class main {
	private static Integer initPop = -1;
	private static String jedisHost = null;
	private static String[] systemQueues = null;

	public static void main(String[] args) {
		main.getCliOptions(args);
		final SimpleTask[] Sys = main.genSystem();
		main.resetState(Sys[0]);
		Sys[0].start();
	}

	public static void resetState(SimpleTask task) {
		MemcachedClient memcachedClient=null;
		try {
			memcachedClient = new MemcachedClient(new InetSocketAddress(main.jedisHost, 11211));
			memcachedClient.flush();
		} catch (IOException e) {
			e.printStackTrace();
		}
		memcachedClient.shutdown();
	}

	public static SimpleTask[] genSystem() {
		HashMap<String, Class> clientEntries = new HashMap<String, Class>();
		HashMap<String, Long> clientEntries_stimes = new HashMap<String, Long>();
		clientEntries.put("think", Client.class);
		clientEntries_stimes.put("think", 1000l);
		final SimpleTask client = new SimpleTask(clientEntries, clientEntries_stimes, main.initPop, "Client",
				main.jedisHost);
		return new SimpleTask[] { client };
	}

	public static boolean validate(final String hostname) {
		return InetAddresses.isUriInetAddress(hostname) || InternetDomainName.isValid(hostname);
	}

	public static void getCliOptions(String[] args) {
		int c;
		LongOpt[] longopts = new LongOpt[3];
		longopts[0] = new LongOpt("initPop", LongOpt.REQUIRED_ARGUMENT, null, 0);
		longopts[1] = new LongOpt("jedisHost", LongOpt.REQUIRED_ARGUMENT, null, 1);
		longopts[2] = new LongOpt("queues", LongOpt.REQUIRED_ARGUMENT, null, 2);

		Getopt g = new Getopt("ddctrl", args, "", longopts);
		g.setOpterr(true);
		while ((c = g.getopt()) != -1) {
			switch (c) {
			case 0:
				try {
					main.initPop = Integer.valueOf(g.getOptarg());
				} catch (NumberFormatException e) {
					System.err.println(String.format("%s is not valid, it must be 0 or 1.", g.getOptarg()));
				}
				break;
			case 1:
				try {
					if (!main.validate(g.getOptarg())) {
						throw new Exception(String.format("%s is not a valid jedis URL", g.getOptarg()));
					}
					main.jedisHost = String.valueOf(g.getOptarg());
				} catch (Exception e) {
					e.printStackTrace();
				}
				break;
			case 2:
				try {
					// Deserialization
					Gson gson = new Gson();
					main.systemQueues = gson.fromJson(String.valueOf(g.getOptarg()), String[].class);
				} catch (Exception e) {
					e.printStackTrace();
				}
				break;
			default:
				break;
			}
		}
	}
}
