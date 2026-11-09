import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import {
  fetchObject,
  formatCalculatedValue,
  parameterRows,
  type CalculatedParameter,
  type CatalogObjectDetail,
  type ColumnMeta,
} from "../api/objects.ts";
import { AladinMap, type SkyFocus } from "../components/AladinMap.tsx";
import { CatalogHeader } from "../components/CatalogHeader.tsx";

export function ObjectPage() {
  const { pgc: pgcParam } = useParams<{ pgc: string }>();
  const pgc = Number(pgcParam);
  const [data, setData] = useState<CatalogObjectDetail | null>(null);
  const [schema, setSchema] = useState<Record<string, ColumnMeta> | null>(null);
  const [derived, setDerived] = useState<CalculatedParameter[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!Number.isFinite(pgc)) {
      setError("Object not found");
      setData(null);
      setSchema(null);
      setDerived([]);
      return;
    }

    let cancelled = false;

    async function load(): Promise<void> {
      try {
        const response = await fetchObject(pgc);
        if (!cancelled) {
          setData(response.data);
          setSchema(response.schema);
          setDerived(response.derived ?? []);
          setError(null);
        }
      } catch (loadError) {
        if (!cancelled) {
          setData(null);
          setSchema(null);
          setDerived([]);
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Failed to load object",
          );
        }
      }
    }

    void load();

    return () => {
      cancelled = true;
    };
  }, [pgc]);

  const rows = useMemo(() => {
    if (data === null || schema === null) {
      return [];
    }
    return parameterRows(data, schema);
  }, [data, schema]);

  const mapObjects = useMemo(() => {
    if (data === null) {
      return [];
    }
    return [
      {
        pgc: data.pgc,
        name: data.name,
        ra: data.ra ?? null,
        dec: data.dec ?? null,
        names: data.names,
      },
    ];
  }, [data]);

  const focus = useMemo((): SkyFocus | null => {
    if (
      data === null ||
      typeof data.ra !== "number" ||
      typeof data.dec !== "number"
    ) {
      return null;
    }
    return { ra: data.ra, dec: data.dec, requestId: data.pgc };
  }, [data]);

  return (
    <main className="catalog">
      <CatalogHeader titleLinksHome />
      {error !== null ? (
        <p className="catalog-status catalog-status-error">{error}</p>
      ) : null}
      {data === null && error === null ? (
        <p className="catalog-status">Loading object…</p>
      ) : null}
      {data !== null ? (
        <>
          <section className="object-identity" aria-label="Object">
            <div className="object-title-row">
              <h2 className="object-title">{data.name}</h2>
              <a
                className="object-hyperleda-link"
                href={`https://leda.sao.ru/object/${data.pgc}`}
                target="_blank"
                rel="noreferrer"
              >
                HyperLEDA
              </a>
            </div>
            {data.names.length > 0 ? (
              <ul className="object-aliases">
                {data.names.map((alias) => (
                  <li key={alias}>{alias}</li>
                ))}
              </ul>
            ) : null}
          </section>
          {focus !== null ? (
            <section className="catalog-sky" aria-label="Sky">
              <AladinMap objects={mapObjects} focus={focus} fov={2} />
            </section>
          ) : null}
          <section className="object-params" aria-label="Parameters">
            <table className="params-table">
              <thead>
                <tr>
                  <th scope="col">Parameter</th>
                  <th scope="col">Unit</th>
                  <th scope="col">Value</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.name}>
                    <th scope="row">
                      <span className="param-name" title={row.description}>
                        {row.name}
                      </span>
                    </th>
                    <td className="param-unit">{row.unit ?? "—"}</td>
                    <td className="param-value">{row.value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
          <section className="object-derived" aria-label="Calculated parameters">
            <h3 className="derived-heading">Calculated Parameters</h3>
            <p className="derived-note">
              Results require validated inputs. A dash means unavailable,
              not zero. Hover over a value for the calculation status.
            </p>
            <table className="params-table">
              <thead>
                <tr>
                  <th scope="col">Parameter</th>
                  <th scope="col">Unit</th>
                  <th scope="col">Value</th>
                </tr>
              </thead>
              <tbody>
                {derived.map((parameter) => (
                  <tr key={parameter.key}>
                    <th scope="row">
                      <span className="param-name" title={parameter.method}>
                        {parameter.label}
                      </span>
                    </th>
                    <td className="param-unit">{parameter.unit ?? "—"}</td>
                    <td
                      className="param-value"
                      title={parameter.reason ?? parameter.method}
                    >
                      {formatCalculatedValue(parameter.value)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </>
      ) : null}
    </main>
  );
}
