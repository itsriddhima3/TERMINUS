package r8p.repo;

import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import r8p.entity.HeaderSlice;

public interface HeaderRepo extends JpaRepository<HeaderSlice, Long> {
  Optional<HeaderSlice> findByPartitionLabelAndExternalBizId(String label, String biz);
}
