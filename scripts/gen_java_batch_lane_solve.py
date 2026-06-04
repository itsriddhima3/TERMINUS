SOLVE_SH = open("/home/riddhima/projects/TERMINUS/tasks/java-batch-lane-reconcile/solution/solve.sh").read()

LANE_FIX_PATCH = """\
--- a/environment/api/src/main/java/k7m/cfg_p9.java
+++ b/environment/api/src/main/java/k7m/cfg_p9.java
@@ -22,7 +22,7 @@
   public DataSource cfg_p9(DataSourceProperties props) {
     HikariDataSource ds = props.initializeDataSourceBuilder().type(HikariDataSource.class).build();
-    ds.setConnectionInitSql("SET TRANSACTION ISOLATION LEVEL READ COMMITTED");
+    ds.setConnectionInitSql("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ");
     return ds;
   }
 }
--- a/environment/db/functions/step_w1.sql
+++ b/environment/db/functions/step_w1.sql
@@ -11,14 +11,14 @@
   IF TG_OP = 'DELETE' THEN
     SELECT h.partition_label INTO hdr FROM header_slice h WHERE h.id = OLD.header_id;
     delta := -OLD.qty;
-    PERFORM 1 FROM line_slice WHERE header_id = OLD.header_id FOR UPDATE;
     PERFORM 1 FROM header_slice WHERE id = OLD.header_id FOR UPDATE;
+    PERFORM 1 FROM line_slice WHERE header_id = OLD.header_id FOR UPDATE;
   ELSIF TG_OP = 'UPDATE' THEN
     SELECT h.partition_label INTO hdr FROM header_slice h WHERE h.id = NEW.header_id;
     delta := NEW.qty - OLD.qty;
-    PERFORM 1 FROM line_slice WHERE id = NEW.id FOR UPDATE;
     PERFORM 1 FROM header_slice WHERE id = NEW.header_id FOR UPDATE;
+    PERFORM 1 FROM line_slice WHERE id = NEW.id FOR UPDATE;
   ELSE
     SELECT h.partition_label INTO hdr FROM header_slice h WHERE h.id = NEW.header_id;
     delta := NEW.qty;
-    PERFORM 1 FROM line_slice WHERE id = NEW.id FOR UPDATE;
     PERFORM 1 FROM header_slice WHERE id = NEW.header_id FOR UPDATE;
+    PERFORM 1 FROM line_slice WHERE id = NEW.id FOR UPDATE;
   END IF;
"""
