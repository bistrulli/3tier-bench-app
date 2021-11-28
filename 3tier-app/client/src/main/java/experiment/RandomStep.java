package experiment;

import java.io.FileWriter;
import java.io.IOException;
import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;
import java.net.InetSocketAddress;
import java.util.ArrayList;
import java.util.Map;
import java.util.Random;
import java.util.concurrent.ExecutionException;

import org.json.JSONArray;

import Server.SimpleTask;
import app.Client;
import net.spy.memcached.MemcachedClient;

public class RandomStep implements Runnable {

	private Integer tick = null;
	private SimpleTask workGenerator = null;
	private Random rnd = null;
	private MemcachedClient memClient = null;
	private ArrayList<Double[]> gkeCtrl = null;

	public RandomStep(SimpleTask workGenerator) {
		this.tick = 0;
		this.workGenerator = workGenerator;
		this.rnd = new Random();
		this.rnd.setSeed(100);
		try {
			this.memClient = new MemcachedClient(new InetSocketAddress(this.workGenerator.getJedisHost(), 11211));
		} catch (IOException e) {
			e.printStackTrace();
		}
		this.gkeCtrl = new ArrayList<Double[]>();
	}

	private void addClients(int delta) {
		int actualSize = this.workGenerator.getThreadpool().getCorePoolSize();
		try {
			this.workGenerator.setThreadPoolSize(actualSize + delta);
		} catch (Exception e1) {
			e1.printStackTrace();
		}
		if (delta >= 0) {
			for (int i = 0; i < delta; i++) {
				Constructor<? extends Runnable> c;
				try {
					c = Client.class.getDeclaredConstructor(SimpleTask.class, Long.class);
					this.workGenerator.getThreadpool().submit(c.newInstance(this.workGenerator, this.workGenerator
							.getsTimes().get(this.workGenerator.getEntries().entrySet().iterator().next().getKey())));
				} catch (NoSuchMethodException | SecurityException | InstantiationException | IllegalAccessException
						| IllegalArgumentException | InvocationTargetException e) {
					e.printStackTrace();
				}
			}
		} else {
			if (Math.abs(delta) > actualSize) {
				System.err.println(String.format("Error killing clients %d-%d", actualSize, Math.abs(delta)));
			}
			try {
				Client.setToKill(Math.abs(delta));
			} catch (Exception e) {
				e.printStackTrace();
			}
		}
	}

	private void tick() {
		// recupero i controlli GKE se non nulli
		Object t1_gke = this.memClient.get("t1_gke");
		Object t2_gke = this.memClient.get("t2_gke");

		if (t1_gke != null && t2_gke != null) {
			String st1_gke = String.valueOf(t1_gke);
			String st2_gke = String.valueOf(t2_gke);
			if (!st1_gke.equals("None") && !st2_gke.equals("None")) {
				System.out.println("found:" + st1_gke + "-" + st2_gke);
				this.gkeCtrl.add(new Double[] { Double.valueOf(st1_gke), Double.valueOf(st2_gke) });
			}
		}

		int nc = 0;
		if (this.tick % 60 == 0) {
			if (this.rnd.nextBoolean()) {
				nc = this.rnd.nextInt(200 - this.workGenerator.getThreadpool().getCorePoolSize());
				System.out.println(
						String.format("delta clients %d-%d", nc, this.workGenerator.getThreadpool().getCorePoolSize()));
				this.addClients(nc);
			} else {
				nc = this.rnd.nextInt(this.workGenerator.getThreadpool().getCorePoolSize());
				System.out.println(String.format("delta clients %d-%d", -nc,
						this.workGenerator.getThreadpool().getCorePoolSize()));
				this.addClients(-nc);
			}
			try {
				this.memClient.set("sim", 3600, "step_" + this.workGenerator.getThreadpool().getCorePoolSize()).get();
			} catch (InterruptedException | ExecutionException e) {
				e.printStackTrace();
			}
		}
		Object end_sim = this.memClient.get("end_sim");
		if (end_sim != null) {
			String send_sim = String.valueOf(end_sim);
			if (send_sim.equals("1")) {
				System.out.println("dumping ctrl trace");
				JSONArray json_array = new JSONArray(this.gkeCtrl);
				FileWriter myWriter;
				try {
					myWriter = new FileWriter("trace.json");
					myWriter.write(json_array.toString());
					myWriter.close();
				} catch (IOException e) {
					e.printStackTrace();
				}
				this.memClient.set("saved", 3600, "1");
			}
		}
		this.tick++;
	}

	@Override
	public void run() {
		this.tick();
	}
}
