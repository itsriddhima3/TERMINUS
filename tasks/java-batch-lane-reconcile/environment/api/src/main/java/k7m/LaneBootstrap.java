package k7m;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;

@SpringBootApplication(scanBasePackages = {"k7m", "r8p", "decoy"})
@EnableJpaRepositories(basePackages = "r8p.repo")
@EntityScan(basePackages = "r8p.entity")
public class LaneBootstrap {
  public static void main(String[] args) {
    SpringApplication.run(LaneBootstrap.class, args);
  }
}
