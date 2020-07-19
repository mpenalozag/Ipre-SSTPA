from gurobipy import Model, GRB, quicksum
from modules.params.params import A, B, N, F, S, I, T, G, R, EL, EV, L, RP, E, EB, V, GT, TIMELIMIT, matches, team_points
from modules.output import parse_output
import time

m = Model("SSTPA")

m.setParam('TimeLimit', TIMELIMIT)

start = time.time()

# x_nf: x[partido, fecha]
# 1 si el partido n se programa finalmente
# en la fecha f
# 0 en otro caso.
x = m.addVars(N, F, vtype=GRB.BINARY, name="x")

# y_is: y[equipo][patron_localias]
# 1 si al equipo i se le asigna el patron
# de localias s
# 0 en otro caso
y = {i: m.addVars(S[i], vtype=GRB.BINARY, name="y") for i in I}

# p_itf: P[equipo, puntos, fecha]
# 1 si el equipo i tiene t puntos al
# finalizar la fecha f.
# 0 en otro caso.
p = m.addVars(I, T, F, vtype=GRB.BINARY, name="p")


# a_if: a[equipo, fecha]
# 1 si el partido del equipo i en la fecha f
# es atractivo por salir campeon.
# 0 en otro caso.
a = m.addVars(I, F, vtype=GRB.BINARY, name="a")

# d_if: d[equipo, fecha]
# 1 si el partido del equipo i en la fecha f
# es atractivo por poder descender.
# 0 en otro caso.
d = m.addVars(I, F, vtype=GRB.BINARY, name="d")


#RESTRICCIONES

#Restriccion 2
m.addConstrs((quicksum(x[n, f] for f in F) == 1 for n in N), name = 'R2')

#Restriccion 3
m.addConstrs((quicksum(x[n, f] for n in N if EL[i][n] + EV[i][n] == 1) == 1 for i in I for f in F), name= 'R3')

#Restriccion 4
for i in I:
	m.addConstr((quicksum(y[i][s] for s in S[i]) == 1), name= 'R4')

#Restriccion 6
for i in I:
	m.addConstrs((quicksum(x[n, f] for n in N if EL[i][n] == 1) == quicksum(y[i][s] for s in S[i] if L[s][f] == 1) for f in F), name='R6') 

#Restriccion 7
for i in I:
	m.addConstrs((quicksum(x[n, f] for n in N if EV[i][n] == 1) == quicksum(y[i][s] for s in S[i] if L[s][f] == 0) for f in F), name='R7')

#Restriccion 8
for i in I:
	m.addConstrs((quicksum(p[i, t, f] for t in T) == 1 for f in F), name='R8')

#Restriccion 9

#Para esta restricción tuvimos que acotar los puntos a menores a 59, ya que si llegara al valor de 62
#se produce KeyError debido a que no esta dentro de nuestro diccionario (nuestro universo).

#Aun no sabemos porque tira errores en los puntos. El output da puntos incoherentes.

for i in I:
	for n in N:
		for t in T:
				for f in F:
					if t < 59:
						if f >= F[0] + 1 and B[i][t][f] == 1 and (EV[i][n] + EL[i][n]) == 1:
							m.addConstr( (p[i, t, f-1] <= quicksum(R[i][n][b]*p[i, t+b, f]+(1-x[n, f]) for b in A)) , name='R9')


#Restriccion 10. Variacion del formato de la R9. Por lo tanto la saltamos por ahora.
for i in I:
	for n in N:
		for t in T:
			for f in F:
				if f == F[0] and t < 59 and B[i][t][f] == 1 and EB[i][t] == 1 and (EV[i][n] + EL[i][n]) == 1:
					m.addConstr( (EB[i][t] <= quicksum(R[i][n][b]*p[i, t+b, f]+(1-x[n, f]) for b in A)) , name='R10')



#Restriccion 12
m.addConstrs((a[i, f] <= 1 - p[i, t, f - 1] + quicksum(p[j, h, f - 1] for h in T if h <= t + 3 * (31 - f)) for i in I
																										   for j in I
																										   for t in T
																										   for f in F
																										   if f > F[0] and j != i), name="R12")

#Restriccion 13
m.addConstrs((a[i, F[0]] <= 1 - EB[i][t] + quicksum(EB[j][h] for h in T if h <= t + 3 * (31 - F[0])) for i in I
																									 for j in I
																									 for t in T
																									 if j != i), name="R13")

#Restriccion 15
m.addConstrs((a[i, f] <= a[i, f - 1] for i in I
									 for f in F
									 if f > F[0]), name="R15")


#Restriccion 16
m.addConstrs((d[i, f] <= 1 - p[i, t, f - 1] + quicksum(p[j, h, f - 1] for h in T if h >= t + 3 * (31 - f)) for i in I
																										   for j in I
																										   for t in T
																										   for f in F
																										   if f > F[0] and j != i), name="R16")

#Restricción 17
m.addConstrs((d[i, F[0]] <= 1 - EB[i][t] + quicksum(EB[j][h] for h in T if h >= t + 3 * (31 - F[0])) for i in I
																									 for j in I
																									 for t in T
																									 if j != i), name="R17")

#Restricción 19
m.addConstrs((d[i, f] <= d[i, f - 1] for i in I
									 for f in F
									 if f > F[0]), name="R19")




#Objetivo que queremos alcanzar al optimizar
m.setObjective(quicksum(quicksum(V[f] * (a[i, f] + d[i, f]) for i in I) for f in F), GRB.MAXIMIZE)
m.optimize()

print(F[0])

parse_output(m.getVars(), matches)