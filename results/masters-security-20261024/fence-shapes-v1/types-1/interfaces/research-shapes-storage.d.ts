/** @module Interface research:shapes/storage **/
export function prepare(value: Request): number;
export interface Request {
  firstFile: File,
  nested?: File,
  batches: Array<File | undefined>,
}

export class File {
  /**
   * This type does not have a public constructor.
   */
  private constructor();
}
