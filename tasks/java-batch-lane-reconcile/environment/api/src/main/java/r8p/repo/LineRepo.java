package r8p.repo;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import r8p.entity.LineSlice;

public interface LineRepo extends JpaRepository<LineSlice, Long> {
  @Query("select count(l) from LineSlice l where l.header.partitionLabel = ?1")
  long countByHeaderPartitionLabel(String label);
}
