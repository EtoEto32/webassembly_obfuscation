/** @module Interface research:fence/storage **/
export function open(id: number): File;
export function prepare(value: Request): number;
export interface Pair {
  source: File,
  destination: File,
}
export interface OptionalWrite {
  primary: File,
  backup?: File,
}
export type Request = RequestRead | RequestWrite | RequestCopy | RequestBatch | RequestOptional | RequestIdle;
export interface RequestRead {
  tag: 'read',
  val: File,
}
export interface RequestWrite {
  tag: 'write',
  val: File,
}
export interface RequestCopy {
  tag: 'copy',
  val: Pair,
}
export interface RequestBatch {
  tag: 'batch',
  val: Array<File>,
}
export interface RequestOptional {
  tag: 'optional',
  val: OptionalWrite,
}
export interface RequestIdle {
  tag: 'idle',
}

export class File {
  /**
   * This type does not have a public constructor.
   */
  private constructor();
}
