package r8p.repo;

import org.springframework.data.jpa.repository.JpaRepository;
import r8p.entity.PartitionDim;

public interface PartitionRepo extends JpaRepository<PartitionDim, String> {}
