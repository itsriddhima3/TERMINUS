package k7m;

import com.zaxxer.hikari.HikariDataSource;
import javax.sql.DataSource;
import org.springframework.boot.autoconfigure.jdbc.DataSourceProperties;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;

@Configuration(value = "k7m_cfg_p9")
public class cfg_p9 {
  @Bean
  @Primary
  @ConfigurationProperties("spring.datasource")
  public DataSourceProperties laneDsProps() {
    return new DataSourceProperties();
  }

  @Bean
  @Primary
  public DataSource cfg_p9(DataSourceProperties props) {
    HikariDataSource ds = props.initializeDataSourceBuilder().type(HikariDataSource.class).build();
    ds.setConnectionInitSql("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ");
    ds.setConnectionTestQuery("SELECT 1");
    return ds;
  }
}
