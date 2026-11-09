export type ColumnMeta = {
  description: string;
  unit?: string | null;
  ucd?: string | null;
};

export type CatalogObject = {
  pgc: number;
  name: string;
  ra: number | null;
  dec: number | null;
  names: string[];
};

export type CatalogObjectDetail = {
  pgc: number;
  name: string;
  ra?: number | null;
  e_ra?: number | null;
  dec?: number | null;
  e_dec?: number | null;
  bt?: number | null;
  e_bt?: number | null;
  kt?: number | null;
  e_kt?: number | null;
  v_hel?: number | null;
  e_v_hel?: number | null;
  v_lg?: number | null;
  e_v_lg?: number | null;
  a50?: number | null;
  e_a50?: number | null;
  b50?: number | null;
  e_b50?: number | null;
  type_name?: string | null;
  dist?: number | null;
  names: string[];
};

type ObjectsListResponse = {
  data: {
    pgc: number[];
    name: string[];
    ra: (number | null)[];
    dec: (number | null)[];
    names: string[][];
  };
};

export type CalculatedParameter = {
  key: string;
  label: string;
  unit: string | null;
  method: string;
  value?: number | string | null;
  status: "available" | "missing_inputs" | "invalid_input" | "not_calculated";
  reason?: string | null;
};

export type ObjectGetResponse = {
  data: CatalogObjectDetail;
  schema: Record<string, ColumnMeta>;
  derived: CalculatedParameter[];
};

export function formatCalculatedValue(
  value: number | string | null | undefined,
): string {
  if (typeof value === "number") {
    return Number.isFinite(value)
      ? String(Number(value.toPrecision(5)))
      : "—";
  }
  return typeof value === "string" ? value : "—";
}

const TABLE_EXCLUDED = new Set(["name", "names"]);

export async function fetchObjects(): Promise<CatalogObject[]> {
  const response = await fetch("/api/v1/objects");
  if (!response.ok) {
    throw new Error(`Failed to load objects (${response.status})`);
  }
  const body = (await response.json()) as ObjectsListResponse;
  const { pgc, name, ra, dec, names } = body.data;
  return pgc.map((id, index) => ({
    pgc: id,
    name: name[index] ?? "",
    ra: ra[index] ?? null,
    dec: dec[index] ?? null,
    names: names[index] ?? [],
  }));
}

export async function fetchObject(pgc: number): Promise<ObjectGetResponse> {
  const response = await fetch(`/api/v1/object/${pgc}`);
  if (response.status === 404) {
    throw new Error("Object not found");
  }
  if (!response.ok) {
    throw new Error(`Failed to load object (${response.status})`);
  }
  return (await response.json()) as ObjectGetResponse;
}

export function matchesQuery(object: CatalogObject, query: string): boolean {
  const normalized = query.trim().toLowerCase();
  if (normalized.length === 0) {
    return true;
  }
  return (
    object.name.toLowerCase().includes(normalized) ||
    String(object.pgc).includes(normalized) ||
    object.names.some((extraName) =>
      extraName.toLowerCase().includes(normalized),
    )
  );
}

export type ParameterRow = {
  name: string;
  description: string;
  unit: string | null;
  value: string;
};

function formatValue(value: unknown): string {
  if (typeof value === "number") {
    return String(value);
  }
  if (typeof value === "string") {
    return value;
  }
  if (value === null || value === undefined) {
    return "";
  }
  return String(value);
}

export function parameterRows(
  data: CatalogObjectDetail,
  schema: Record<string, ColumnMeta>,
): ParameterRow[] {
  const record = data as Record<string, unknown>;
  const rows: ParameterRow[] = [];
  for (const [key, meta] of Object.entries(schema)) {
    if (TABLE_EXCLUDED.has(key) || !(key in record)) {
      continue;
    }
    rows.push({
      name: key,
      description: meta.description,
      unit: meta.unit ?? null,
      value: formatValue(record[key]),
    });
  }
  return rows;
}
