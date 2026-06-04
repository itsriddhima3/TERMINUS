<?php
declare(strict_types=1);

/** Lists tables without column detail — not used by guardctl. */
final class SchemaProbe
{
    public static function tables(PDO $db): array
    {
        $rows = $db->query(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )->fetchAll(PDO::FETCH_COLUMN);
        return $rows ?: [];
    }
}
