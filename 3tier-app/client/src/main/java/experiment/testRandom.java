package experiment;

import org.apache.commons.math3.distribution.ExponentialDistribution;

public class testRandom {

	public static void main(String[] args) {
		ExponentialDistribution exp=new ExponentialDistribution(1.0);
		for (int i = 0; i < 10; i++) {
			System.out.println(exp.sample());			
		}

	}

}
