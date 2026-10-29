/** @module Interface research:shapes/storage **/
export function prepare(value: Request): number;
export interface Request {
  firstFile: File,
  nested?: Option<File | undefined>,
  batches: Array<File | undefined>,
}
export type Option<T> = { tag: 'none' } | { tag: 'some', val: T };

export class File {
  /**
   * This type does not have a public constructor.
   */
  private constructor();
}
