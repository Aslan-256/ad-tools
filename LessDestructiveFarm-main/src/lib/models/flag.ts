import { Column, Model, Table, Index, DataType } from 'sequelize-typescript';
import { Field, ObjectType } from 'type-graphql';

export type FlagState = 'QUEUED' | 'SKIPPED' | 'ACCEPTED' | 'REJECTED';

@ObjectType()
@Table
export default class Flag extends Model<Flag> {
  @Field()
  @Column({ primaryKey: true, unique: true, type: DataType.TEXT })
  flag!: string;

  @Field()
  @Column({ allowNull: false, type: DataType.TEXT })
  sploit!: string;

  @Field()
  @Column({ allowNull: false, type: DataType.TEXT })
  team!: string;

  @Field()
  @Column({ allowNull: false })
  @Index({ name: 'Flag_status_timestamp' })
  timestamp!: Date;

  @Field({ nullable: true })
  @Column({ allowNull: true, defaultValue: 'QUEUED' })
  @Index({
    where: { status: 'QUEUED' }
  })
  @Index({ name: 'Flag_status_timestamp' })
  status!: FlagState;

  @Field({ nullable: true })
  @Column({ allowNull: true, type: DataType.TEXT })
  checksystem_response!: string;
}
